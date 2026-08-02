#include "chlm.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHLM_VERSION 1u
#define CHLM_ENDIAN 0x1234u
#define CHLM_HEADER_BYTES 64u
#define CHLM_ENTRY_BYTES 64u
#define CHLM_FLOAT32 1u
#define CHLM_ROW_INT8 2u
#define CHLM_MAX_LAYERS 16u

#pragma pack(push, 1)
typedef struct {
    char magic[4]; uint16_t version, endian;
    uint32_t header_bytes, entry_bytes, tensor_count;
    uint32_t vocab, width, layers, lanes, state_width, mixer_width, context;
    float norm_epsilon;
    uint32_t directory_offset, data_offset, payload_crc32;
} DiskHeader;

typedef struct {
    uint32_t name_hash; uint8_t dtype, rank; uint16_t reserved0;
    uint32_t dims[4];
    uint32_t data_offset, data_bytes, scale_offset, scale_bytes;
    uint32_t data_crc32, scale_crc32, reserved[4];
} DiskEntry;
#pragma pack(pop)

typedef struct { const DiskEntry *entry; const uint8_t *data; const float *scales; } Tensor;
typedef struct {
    Tensor down, fact_output, fact_router_bias, fact_router, gate_bias, gate;
    Tensor post_norm, pre_norm, proposal_bias, proposal, recurrent_scale;
    Tensor router_bias, router, state_output, value_bias, value, write_bias, write;
} Layer;

struct chlm_model {
    const uint8_t *image; size_t image_bytes; DiskHeader header;
    const DiskEntry *entries; Tensor embedding, final_norm, output_bias;
    Layer layers[CHLM_MAX_LAYERS];
    float *state, *scratch; size_t scratch_count;
    char error[160];
};

static uint32_t crc32_bytes(const uint8_t *data, size_t length) {
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t i = 0; i < length; ++i) {
        crc ^= data[i];
        for (int bit = 0; bit < 8; ++bit) crc = (crc >> 1) ^ (0xEDB88320u & (uint32_t)-(int32_t)(crc & 1u));
    }
    return ~crc;
}

static uint32_t fnv1a(const char *text) {
    uint32_t value = 2166136261u;
    while (*text) { value = (value ^ (uint8_t)*text++) * 16777619u; }
    return value;
}

static int fail(chlm_model *model, const char *message) {
    snprintf(model->error, sizeof(model->error), "%s", message); return -1;
}

static int bounds(size_t total, uint32_t offset, uint32_t length) {
    return offset <= total && length <= total - offset;
}

static int bind_hash(chlm_model *model, uint32_t hash, Tensor *tensor) {
    for (uint32_t i = 0; i < model->header.tensor_count; ++i) {
        const DiskEntry *entry = &model->entries[i];
        if (entry->name_hash != hash) continue;
        if (!bounds(model->image_bytes, entry->data_offset, entry->data_bytes)) return fail(model, "tensor data out of bounds");
        if (entry->scale_bytes && !bounds(model->image_bytes, entry->scale_offset, entry->scale_bytes)) return fail(model, "tensor scales out of bounds");
        const uint8_t *data = model->image + entry->data_offset;
        const uint8_t *scales = entry->scale_bytes ? model->image + entry->scale_offset : NULL;
        if (crc32_bytes(data, entry->data_bytes) != entry->data_crc32) return fail(model, "tensor data CRC mismatch");
        if (entry->scale_bytes && crc32_bytes(scales, entry->scale_bytes) != entry->scale_crc32) return fail(model, "tensor scale CRC mismatch");
        tensor->entry = entry; tensor->data = data; tensor->scales = (const float *)scales; return 0;
    }
    return fail(model, "required tensor missing");
}

static int bind_name(chlm_model *model, const char *name, Tensor *tensor) { return bind_hash(model, fnv1a(name), tensor); }

static int bind_layer(chlm_model *m, uint32_t index, Layer *l) {
    char name[96];
#define BIND(field, suffix) do { snprintf(name, sizeof(name), "blocks.%u.%s", index, suffix); if (bind_name(m, name, &l->field)) return -1; } while (0)
    BIND(down, "down.weight"); BIND(fact_output, "fact_output.weight");
    BIND(fact_router_bias, "fact_router.bias"); BIND(fact_router, "fact_router.weight");
    BIND(gate_bias, "gate.bias"); BIND(gate, "gate.weight"); BIND(post_norm, "post_norm.scale");
    BIND(pre_norm, "pre_norm.scale"); BIND(proposal_bias, "proposal.bias"); BIND(proposal, "proposal.weight");
    BIND(recurrent_scale, "recurrent_scale"); BIND(router_bias, "router.bias"); BIND(router, "router.weight");
    BIND(state_output, "state_output.weight"); BIND(value_bias, "value.bias"); BIND(value, "value.weight");
    BIND(write_bias, "write.bias"); BIND(write, "write.weight");
#undef BIND
    return 0;
}

static void matvec(const Tensor *tensor, const float *input, float *output) {
    uint32_t rows = 1; for (uint8_t i = 0; i + 1 < tensor->entry->rank; ++i) rows *= tensor->entry->dims[i];
    uint32_t columns = tensor->entry->dims[tensor->entry->rank - 1];
    const int8_t *codes = (const int8_t *)tensor->data;
    for (uint32_t row = 0; row < rows; ++row) {
        float sum = 0.0f;
        for (uint32_t column = 0; column < columns; ++column) sum += (float)codes[(size_t)row * columns + column] * input[column];
        output[row] = sum * tensor->scales[row];
    }
}

static float tensor_value(const Tensor *tensor, uint32_t index) {
    if (tensor->entry->dtype == CHLM_FLOAT32) return ((const float *)tensor->data)[index];
    uint32_t columns = tensor->entry->dims[tensor->entry->rank - 1];
    return (float)((const int8_t *)tensor->data)[index] * tensor->scales[index / columns];
}

static void linear(const Tensor *weight, const Tensor *bias, const float *input, float *output) {
    matvec(weight, input, output);
    if (bias && bias->entry) {
        uint32_t rows = weight->entry->dims[0]; const float *values = (const float *)bias->data;
        for (uint32_t i = 0; i < rows; ++i) output[i] += values[i];
    }
}

static void rms_norm(const float *input, const Tensor *scale, float epsilon, uint32_t width, float *output) {
    float energy = 0.0f; for (uint32_t i = 0; i < width; ++i) energy += input[i] * input[i];
    float factor = 1.0f / sqrtf(energy / (float)width + epsilon); const float *weights = (const float *)scale->data;
    for (uint32_t i = 0; i < width; ++i) output[i] = input[i] * factor * weights[i];
}

static void softmax(float *values, uint32_t count) {
    float maximum = values[0]; for (uint32_t i = 1; i < count; ++i) if (values[i] > maximum) maximum = values[i];
    float total = 0.0f; for (uint32_t i = 0; i < count; ++i) { values[i] = expf(values[i] - maximum); total += values[i]; }
    for (uint32_t i = 0; i < count; ++i) values[i] /= total;
}

static int finite_vector(const float *values, uint32_t count) {
    for (uint32_t i = 0; i < count; ++i) if (!isfinite(values[i])) return 0;
    return 1;
}

int chlm_create(chlm_model **output, const void *image, size_t image_bytes) {
    if (!output || !image || image_bytes < CHLM_HEADER_BYTES) return -1;
    chlm_model *m = (chlm_model *)calloc(1, sizeof(*m)); if (!m) return -1;
    m->image = (const uint8_t *)image; m->image_bytes = image_bytes; memcpy(&m->header, image, sizeof(m->header));
    if (memcmp(m->header.magic, "CHLM", 4) || m->header.version != CHLM_VERSION || m->header.endian != CHLM_ENDIAN) { fail(m, "invalid CHLM header"); goto error; }
    if (m->header.header_bytes != CHLM_HEADER_BYTES || m->header.entry_bytes != CHLM_ENTRY_BYTES || m->header.layers > CHLM_MAX_LAYERS) { fail(m, "unsupported CHLM dimensions"); goto error; }
    if (!bounds(image_bytes, m->header.directory_offset, m->header.tensor_count * CHLM_ENTRY_BYTES) || m->header.data_offset > image_bytes) { fail(m, "CHLM directory out of bounds"); goto error; }
    if (crc32_bytes(m->image + m->header.data_offset, image_bytes - m->header.data_offset) != m->header.payload_crc32) { fail(m, "CHLM payload CRC mismatch"); goto error; }
    m->entries = (const DiskEntry *)(m->image + m->header.directory_offset);
    if (bind_name(m, "embedding.weight", &m->embedding) || bind_name(m, "final_norm.scale", &m->final_norm) || bind_name(m, "output_bias", &m->output_bias)) goto error;
    for (uint32_t i = 0; i < m->header.layers; ++i) if (bind_layer(m, i, &m->layers[i])) goto error;
    size_t state_count = (size_t)m->header.layers * 2u * m->header.lanes * m->header.state_width;
    m->scratch_count = (size_t)m->header.width * 8u + (size_t)m->header.mixer_width * 3u + (size_t)m->header.lanes * m->header.state_width * 4u;
    m->state = (float *)calloc(state_count, sizeof(float)); m->scratch = (float *)calloc(m->scratch_count, sizeof(float));
    if (!m->state || !m->scratch) { fail(m, "allocation failed"); goto error; }
    *output = m; return 0;
error:
    *output = m; return -1;
}

void chlm_destroy(chlm_model *m) { if (m) { free(m->state); free(m->scratch); free(m); } }
void chlm_reset(chlm_model *m) { if (m && m->state) memset(m->state, 0, (size_t)m->header.layers * 2u * m->header.lanes * m->header.state_width * sizeof(float)); }
uint32_t chlm_vocab_size(const chlm_model *m) { return m ? m->header.vocab : 0; }
const char *chlm_last_error(const chlm_model *m) { return m ? m->error : "no model"; }

int chlm_step(chlm_model *m, uint32_t token_id, float *logits, size_t logits_count) {
    if (!m || token_id >= m->header.vocab || !logits || logits_count < m->header.vocab) return -1;
    const uint32_t d=m->header.width, k=m->header.lanes, s=m->header.state_width, ks=k*s, f=m->header.mixer_width;
    float *p=m->scratch, *token=p; p+=d; float *norm=p; p+=d; float *a=p; p+=ks; float *b=p; p+=ks;
    float *route=p; p+=k; float *fact_route=p; p+=k; float *routed=p; p+=ks; float *fact_routed=p; p+=ks;
    float *out=p; p+=d; float *fact_out=p; p+=d; float *gate=p; p+=f; float *value=p; p+=f; float *mixed=p; p+=f; float *down=p;
    if ((size_t)(down + d - m->scratch) > m->scratch_count) return fail(m, "scratch overflow");
    const int8_t *embedding=(const int8_t *)m->embedding.data; float emb_scale=m->embedding.scales[token_id];
    for(uint32_t i=0;i<d;++i) token[i]=(float)embedding[(size_t)token_id*d+i]*emb_scale;
    if(!finite_vector(token,d)) return fail(m,"non-finite embedding");
    if(token_id==3u) chlm_reset(m);
    for(uint32_t layer_index=0;layer_index<m->header.layers;++layer_index){
        Layer *l=&m->layers[layer_index]; float *state=m->state+(size_t)layer_index*2u*ks; float *working=state,*fact=state+ks;
        rms_norm(token,&l->pre_norm,m->header.norm_epsilon,d,norm);
        linear(&l->proposal,&l->proposal_bias,norm,a); linear(&l->write,&l->write_bias,norm,b);
        if(!finite_vector(a,ks)||!finite_vector(b,ks)) return fail(m,"non-finite state projection");
        for(uint32_t i=0;i<ks;++i){ float proposal=tanhf(a[i]+tensor_value(&l->recurrent_scale,i)*working[i]); float write=1.0f/(1.0f+expf(-b[i])); working[i]+=write*(proposal-working[i]); }
        if(!finite_vector(working,ks)||!finite_vector(fact,ks)) return fail(m,"non-finite recurrent state");
        linear(&l->router,&l->router_bias,norm,route); softmax(route,k);
        linear(&l->fact_router,&l->fact_router_bias,norm,fact_route); softmax(fact_route,k);
        if(!finite_vector(route,k)||!finite_vector(fact_route,k)) return fail(m,"non-finite router");
        for(uint32_t lane=0;lane<k;++lane) for(uint32_t i=0;i<s;++i){ uint32_t q=lane*s+i; routed[q]=working[q]*route[lane]; fact_routed[q]=fact[q]*fact_route[lane]; }
        if(!finite_vector(routed,ks)||!finite_vector(fact_routed,ks)) return fail(m,"non-finite routed state");
        matvec(&l->state_output,routed,out); matvec(&l->fact_output,fact_routed,fact_out);
        if(!finite_vector(out,d)||!finite_vector(fact_out,d)){snprintf(m->error,sizeof(m->error),"non-finite state output layer %u out0=%g fact0=%g",layer_index,out[0],fact_out[0]);return -1;}
        for(uint32_t i=0;i<d;++i) token[i]+=out[i]+fact_out[i];
        rms_norm(token,&l->post_norm,m->header.norm_epsilon,d,norm);
        linear(&l->gate,&l->gate_bias,norm,gate); linear(&l->value,&l->value_bias,norm,value);
        if(!finite_vector(gate,f)||!finite_vector(value,f)) return fail(m,"non-finite mixer projection");
        for(uint32_t i=0;i<f;++i){ float sig=1.0f/(1.0f+expf(-gate[i])); mixed[i]=gate[i]*sig*value[i]; }
        if(!finite_vector(mixed,f)) return fail(m,"non-finite mixer product");
        matvec(&l->down,mixed,down); for(uint32_t i=0;i<d;++i) token[i]+=down[i];
        if(!finite_vector(token,d)) return fail(m,"non-finite layer output");
        if(token_id==4u) memcpy(fact,working,ks*sizeof(float));
    }
    rms_norm(token,&m->final_norm,m->header.norm_epsilon,d,norm); matvec(&m->embedding,norm,logits);
    if(!finite_vector(norm,d)||!finite_vector(logits,m->header.vocab)) return fail(m,"non-finite final output");
    const float *bias=(const float *)m->output_bias.data; for(uint32_t i=0;i<m->header.vocab;++i) logits[i]+=bias[i];
    return 0;
}
