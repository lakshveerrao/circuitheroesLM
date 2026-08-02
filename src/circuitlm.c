#include "circuitlm.h"

#include <string.h>

#define LLM_INT8_ACT 1
#include "circuitlm_ple_runtime.h"

struct circuitlm {
    Model model;
    Scratch scratch;
    circuitlm_alloc_fn allocate;
    circuitlm_free_fn release;
    void *memory_user;
};

static void *take(circuitlm_t *lm, size_t count, size_t width)
{
    if (count == 0 || width > SIZE_MAX / count) return NULL;
    void *memory = lm->allocate(lm->memory_user, count * width);
    if (memory) memset(memory, 0, count * width);
    return memory;
}

static int scratch_create(circuitlm_t *lm)
{
    Cfg *c = &lm->model.c;
    Scratch *s = &lm->scratch;
    size_t d = (size_t)c->dim, l = (size_t)c->n_layers;
    size_t p = (size_t)c->ple_dim, f = (size_t)c->ffn;
    size_t v = (size_t)c->vocab, n = (size_t)c->seq_len;
    s->x = take(lm, d, sizeof(float));
    s->h = take(lm, f > d ? f : d, sizeof(float));
    s->qkv = take(lm, 3 * d, sizeof(float));
    s->att = take(lm, d, sizeof(float));
    s->g1 = take(lm, f, sizeof(float));
    s->g2 = take(lm, p > f ? p : f, sizeof(float));
    s->ple = take(lm, l * p, sizeof(float));
    s->tmpP = take(lm, l * p, sizeof(float));
    s->trow = take(lm, l * p, sizeof(float));
    s->logits = take(lm, v, sizeof(float));
    s->scores = take(lm, n, sizeof(float));
    s->kcache = take(lm, l * n * d, sizeof(float));
    s->vcache = take(lm, l * n * d, sizeof(float));
    return s->x && s->h && s->qkv && s->att && s->g1 && s->g2 && s->ple &&
           s->tmpP && s->trow && s->logits && s->scores && s->kcache && s->vcache;
}

static void scratch_destroy(circuitlm_t *lm)
{
    Scratch *s = &lm->scratch;
    void *items[] = {s->x, s->h, s->qkv, s->att, s->g1, s->g2, s->ple,
                     s->tmpP, s->trow, s->logits, s->scores, s->kcache, s->vcache};
    for (size_t i = 0; i < sizeof(items) / sizeof(items[0]); ++i)
        if (items[i]) lm->release(lm->memory_user, items[i]);
    memset(s, 0, sizeof(*s));
}

circuitlm_status_t circuitlm_create(const circuitlm_config_t *config,
                                    circuitlm_t **instance)
{
    if (!config || !instance || !config->model_data || config->model_bytes < 40 ||
        !config->allocate || !config->release)
        return CIRCUITLM_ERROR_ARGUMENT;
    circuitlm_t *lm = config->allocate(config->memory_user, sizeof(*lm));
    if (!lm) return CIRCUITLM_ERROR_MEMORY;
    memset(lm, 0, sizeof(*lm));
    lm->allocate = config->allocate;
    lm->release = config->release;
    lm->memory_user = config->memory_user;
    if (llm_load(config->model_data, &lm->model) != 0 ||
        lm->model.c.n_layers > 32 || lm->model.c.seq_len < 2) {
        config->release(config->memory_user, lm);
        return CIRCUITLM_ERROR_MODEL;
    }
    if (!scratch_create(lm)) {
        scratch_destroy(lm);
        config->release(config->memory_user, lm);
        return CIRCUITLM_ERROR_MEMORY;
    }
    *instance = lm;
    return CIRCUITLM_OK;
}

void circuitlm_destroy(circuitlm_t *lm)
{
    if (!lm) return;
    circuitlm_free_fn release = lm->release;
    void *user = lm->memory_user;
    scratch_destroy(lm);
    release(user, lm);
}

circuitlm_status_t circuitlm_model_info(const circuitlm_t *lm,
                                        circuitlm_model_info_t *info)
{
    if (!lm || !info) return CIRCUITLM_ERROR_ARGUMENT;
    Cfg c = lm->model.c;
    uint64_t parameters = (uint64_t)c.vocab * c.dim +
        (uint64_t)c.n_layers * c.ple_dim * c.dim + c.ple_dim +
        (uint64_t)c.vocab * c.n_layers * c.ple_dim +
        (uint64_t)c.n_layers * (c.dim + 4 * c.dim * c.dim + c.dim +
        3 * c.ffn * c.dim + 2 * c.ple_dim * c.dim + c.dim) + c.dim;
    info->parameters = parameters > UINT32_MAX ? UINT32_MAX : (uint32_t)parameters;
    info->vocabulary = (uint16_t)c.vocab;
    info->context_tokens = (uint16_t)c.seq_len;
    info->hidden_size = (uint16_t)c.dim;
    info->layers = (uint8_t)c.n_layers;
    info->attention_heads = (uint8_t)c.n_heads;
    return CIRCUITLM_OK;
}

circuitlm_status_t circuitlm_generate(circuitlm_t *lm, const uint16_t *prompt,
                                      size_t prompt_tokens, size_t maximum_new_tokens,
                                      circuitlm_token_fn on_token, void *token_user)
{
    if (!lm || !prompt || !prompt_tokens || !on_token)
        return CIRCUITLM_ERROR_ARGUMENT;
    if (prompt_tokens + maximum_new_tokens > (size_t)lm->model.c.seq_len)
        return CIRCUITLM_ERROR_CONTEXT;
    Scratch *s = &lm->scratch;
    size_t cache = (size_t)lm->model.c.n_layers * lm->model.c.seq_len *
                   lm->model.c.dim * sizeof(float);
    memset(s->kcache, 0, cache);
    memset(s->vcache, 0, cache);
    int position = 0;
    for (size_t i = 0; i < prompt_tokens; ++i)
        llm_forward(&lm->model, prompt[i], position++, s);
    for (size_t step = 0; step < maximum_new_tokens; ++step) {
        int best = 0;
        float score = -1.0e30f;
        for (int token = 0; token < lm->model.c.vocab; ++token) {
            if (s->logits[token] > score) {
                score = s->logits[token];
                best = token;
            }
        }
        if (best == 0 || on_token(token_user, (uint16_t)best) != 0) break;
        llm_forward(&lm->model, best, position++, s);
    }
    return CIRCUITLM_OK;
}
