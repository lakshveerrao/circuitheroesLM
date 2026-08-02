#ifndef CIRCUITHEROESLM_CHTK_H
#define CIRCUITHEROESLM_CHTK_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct chlm_tokenizer chlm_tokenizer;

int chlm_tokenizer_create(chlm_tokenizer **output, const void *image, size_t image_bytes);
void chlm_tokenizer_destroy(chlm_tokenizer *tokenizer);
const char *chlm_tokenizer_last_error(const chlm_tokenizer *tokenizer);
uint32_t chlm_tokenizer_vocab_size(const chlm_tokenizer *tokenizer);
int chlm_tokenizer_encode(const chlm_tokenizer *tokenizer, const char *text,
                          uint16_t *tokens, size_t capacity, size_t *token_count);
int chlm_tokenizer_piece(const chlm_tokenizer *tokenizer, uint16_t token,
                         const uint8_t **piece, size_t *piece_bytes);

#ifdef __cplusplus
}
#endif
#endif
