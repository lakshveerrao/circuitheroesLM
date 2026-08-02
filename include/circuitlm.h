#pragma once

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct circuitlm circuitlm_t;

typedef enum {
    CIRCUITLM_OK = 0,
    CIRCUITLM_ERROR_ARGUMENT = -1,
    CIRCUITLM_ERROR_MODEL = -2,
    CIRCUITLM_ERROR_MEMORY = -3,
    CIRCUITLM_ERROR_CONTEXT = -4
} circuitlm_status_t;

typedef void *(*circuitlm_alloc_fn)(void *user, size_t bytes);
typedef void (*circuitlm_free_fn)(void *user, void *memory);
typedef int (*circuitlm_token_fn)(void *user, uint16_t token);

typedef struct {
    const uint8_t *model_data;
    size_t model_bytes;
    circuitlm_alloc_fn allocate;
    circuitlm_free_fn release;
    void *memory_user;
} circuitlm_config_t;

typedef struct {
    uint32_t parameters;
    uint16_t vocabulary;
    uint16_t context_tokens;
    uint16_t hidden_size;
    uint8_t layers;
    uint8_t attention_heads;
} circuitlm_model_info_t;

circuitlm_status_t circuitlm_create(const circuitlm_config_t *config,
                                    circuitlm_t **instance);
void circuitlm_destroy(circuitlm_t *instance);
circuitlm_status_t circuitlm_model_info(const circuitlm_t *instance,
                                        circuitlm_model_info_t *info);
circuitlm_status_t circuitlm_generate(circuitlm_t *instance,
                                      const uint16_t *prompt,
                                      size_t prompt_tokens,
                                      size_t maximum_new_tokens,
                                      circuitlm_token_fn on_token,
                                      void *token_user);

#ifdef __cplusplus
}
#endif
