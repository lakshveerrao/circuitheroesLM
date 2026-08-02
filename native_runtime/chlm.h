#ifndef CIRCUITHEROESLM_CHLM_H
#define CIRCUITHEROESLM_CHLM_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct chlm_model chlm_model;

int chlm_create(chlm_model **output, const void *image, size_t image_bytes);
void chlm_destroy(chlm_model *model);
void chlm_reset(chlm_model *model);
int chlm_step(chlm_model *model, uint32_t token_id, float *logits, size_t logits_count);
uint32_t chlm_vocab_size(const chlm_model *model);
uint32_t chlm_context_size(const chlm_model *model);
const char *chlm_last_error(const chlm_model *model);

#ifdef __cplusplus
}
#endif
#endif
