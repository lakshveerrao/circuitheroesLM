#ifndef CIRCUITHEROESLM_GENERATION_H
#define CIRCUITHEROESLM_GENERATION_H

#include "chlm.h"
#include "chlm_tokenizer.h"

#include <stddef.h>
#include <stdint.h>

typedef struct {
    const char *name;
    const char *family;
    const char *purpose;
    const char *symbol;
    const char *behavior;
    const char *constraint;
} chlm_fact_fields;

int chlm_generate_grounded(chlm_model *model, const chlm_tokenizer *tokenizer,
                           const char *prompt, const chlm_fact_fields *fields,
                           uint32_t max_new_tokens, char *output, size_t output_bytes,
                           uint32_t *generated_tokens);

#endif
