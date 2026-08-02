#include "chlm_generation.h"

#include <float.h>
#include <stdlib.h>
#include <string.h>

#define CHLM_PROMPT_CAPACITY 2048u

static const char *copy_field(uint16_t token, const chlm_fact_fields *fields) {
    if (!fields) return NULL;
    switch (token) {
        case 7: return fields->name;
        case 8: return fields->family;
        case 9: return fields->purpose;
        case 10: return fields->symbol;
        case 11: return fields->behavior;
        case 12: return fields->constraint;
        default: return NULL;
    }
}

static int append(char *output, size_t output_bytes, size_t *used,
                  const void *data, size_t data_bytes) {
    if (!data || *used + data_bytes >= output_bytes) return -1;
    memcpy(output + *used, data, data_bytes);
    *used += data_bytes;
    output[*used] = '\0';
    return 0;
}

int chlm_generate_grounded(chlm_model *model, const chlm_tokenizer *tokenizer,
                           const char *prompt, const chlm_fact_fields *fields,
                           uint32_t max_new_tokens, char *output, size_t output_bytes,
                           uint32_t *generated_tokens) {
    if (!model || !tokenizer || !prompt || !output || output_bytes < 2u ||
        max_new_tokens == 0 || max_new_tokens > 256u ||
        chlm_vocab_size(model) != chlm_tokenizer_vocab_size(tokenizer)) return -1;
    uint16_t *tokens = (uint16_t *)calloc(CHLM_PROMPT_CAPACITY + max_new_tokens, sizeof(uint16_t));
    float *logits = (float *)malloc((size_t)chlm_vocab_size(model) * sizeof(float));
    if (!tokens || !logits) { free(tokens); free(logits); return -1; }
    tokens[0] = 1u;
    size_t prompt_count = 0;
    if (chlm_tokenizer_encode(tokenizer, prompt, tokens + 1u, CHLM_PROMPT_CAPACITY - 1u,
                              &prompt_count)) { free(tokens); free(logits); return -1; }
    prompt_count += 1u;
    size_t start = prompt_count > chlm_context_size(model) ? prompt_count - chlm_context_size(model) : 0u;
    chlm_reset(model);
    for (size_t index = start; index < prompt_count; ++index) {
        if (chlm_step(model, tokens[index], logits, chlm_vocab_size(model))) {
            free(tokens); free(logits); return -1;
        }
    }
    uint32_t generated = 0;
    while (generated < max_new_tokens) {
        uint16_t best = 2u;
        float best_score = -FLT_MAX;
        for (uint32_t token = 2u; token < chlm_vocab_size(model); ++token) {
            if (logits[token] > best_score) { best_score = logits[token]; best = (uint16_t)token; }
        }
        if (best == 2u) break;
        tokens[prompt_count + generated++] = best;
        if (chlm_step(model, best, logits, chlm_vocab_size(model))) {
            free(tokens); free(logits); return -1;
        }
    }
    output[0] = '\0';
    size_t used = 0;
    for (uint32_t index = 0; index < generated; ++index) {
        uint16_t token = tokens[prompt_count + index];
        const char *field = copy_field(token, fields);
        if (token >= 7u && token <= 12u) {
            if (!field || append(output, output_bytes, &used, field, strlen(field))) goto error;
        } else if (token >= 13u) {
            const uint8_t *piece = NULL;
            size_t piece_bytes = 0;
            if (chlm_tokenizer_piece(tokenizer, token, &piece, &piece_bytes) ||
                append(output, output_bytes, &used, piece, piece_bytes)) goto error;
        }
    }
    while (used && (output[used - 1u] == ' ' || output[used - 1u] == '\n' || output[used - 1u] == '\r' || output[used - 1u] == '\t'))
        output[--used] = '\0';
    size_t leading = 0;
    while (leading < used && (output[leading] == ' ' || output[leading] == '\n' || output[leading] == '\r' || output[leading] == '\t')) leading++;
    if (leading) { memmove(output, output + leading, used - leading + 1u); used -= leading; }
    if (generated_tokens) *generated_tokens = generated;
    free(tokens); free(logits);
    return used ? 0 : -1;
error:
    output[0] = '\0';
    free(tokens); free(logits);
    return -1;
}
