#include "chlm.h"
#include "chlm_generation.h"
#include "chlm_tokenizer.h"

#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_partition.h"
#include "esp_timer.h"

/* Native hardware-in-the-loop numerical and timing probe. */
static const char *TAG = "circuitheroesLM";
extern const uint8_t golden_bin_start[] asm("_binary_golden_bin_start");
extern const uint8_t golden_bin_end[] asm("_binary_golden_bin_end");
extern const uint8_t tokenizer_chtk_start[] asm("_binary_tokenizer_chtk_start");
extern const uint8_t tokenizer_chtk_end[] asm("_binary_tokenizer_chtk_end");

void app_main(void) {
    ESP_LOGI(TAG, "native Engineering State Router + FactTape probe");
    const esp_partition_t *partition = esp_partition_find_first(
        ESP_PARTITION_TYPE_DATA, 0x40, "model");
    if (!partition) {
        ESP_LOGE(TAG, "native CHLM model partition not found");
        return;
    }
    const void *mapped = NULL;
    esp_partition_mmap_handle_t mapping = 0;
    esp_err_t map_error = esp_partition_mmap(
        partition, 0, partition->size, ESP_PARTITION_MMAP_DATA, &mapped, &mapping);
    if (map_error != ESP_OK) {
        ESP_LOGE(TAG, "model mmap failed: %s", esp_err_to_name(map_error));
        return;
    }
    chlm_model *model = NULL;
    if (chlm_create(&model, mapped, partition->size)) {
        ESP_LOGE(TAG, "CHLM load failed: %s", chlm_last_error(model));
        chlm_destroy(model);
        esp_partition_munmap(mapping);
        return;
    }
    chlm_tokenizer *tokenizer = NULL;
    const size_t tokenizer_bytes = (size_t)(tokenizer_chtk_end - tokenizer_chtk_start);
    if (chlm_tokenizer_create(&tokenizer, tokenizer_chtk_start, tokenizer_bytes) ||
        chlm_tokenizer_vocab_size(tokenizer) != chlm_vocab_size(model)) {
        ESP_LOGE(TAG, "CHTK load failed: %s", chlm_tokenizer_last_error(tokenizer));
        return;
    }
    const size_t golden_size = (size_t)(golden_bin_end - golden_bin_start);
    if (golden_size < 12 || memcmp(golden_bin_start, "CHLG", 4)) {
        uint32_t magic = 0;
        if (golden_size >= sizeof(magic)) memcpy(&magic, golden_bin_start, sizeof(magic));
        ESP_LOGE(TAG, "embedded golden is invalid: bytes=%lu magic=%08lx",
                 (unsigned long)golden_size, (unsigned long)magic);
        return;
    }
    uint16_t token_count = 0;
    uint32_t golden_vocab = 0;
    memcpy(&token_count, golden_bin_start + 6, sizeof(token_count));
    memcpy(&golden_vocab, golden_bin_start + 8, sizeof(golden_vocab));
    if (golden_vocab != chlm_vocab_size(model) ||
        golden_size != 12u + (size_t)token_count * 4u + (size_t)golden_vocab * 4u) {
        ESP_LOGE(TAG, "golden/model dimension mismatch");
        return;
    }
    float *logits = heap_caps_malloc((size_t)golden_vocab * sizeof(float),
                                     MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (!logits) logits = malloc((size_t)golden_vocab * sizeof(float));
    if (!logits) {
        ESP_LOGE(TAG, "logit allocation failed");
        return;
    }
    const uint32_t *tokens = (const uint32_t *)(golden_bin_start + 12);
    const float *expected = (const float *)(golden_bin_start + 12 + (size_t)token_count * 4u);
    const uint32_t repetitions = 100u;
    const size_t internal_before = heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
    const size_t psram_before = heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
    int64_t started = esp_timer_get_time();
    float maximum = 0.0f, mean = 0.0f;
    for (uint32_t repetition = 0; repetition < repetitions; ++repetition) {
        chlm_reset(model);
        for (uint16_t index = 0; index < token_count; ++index) {
            if (chlm_step(model, tokens[index], logits, golden_vocab)) {
                ESP_LOGE(TAG, "native sequence %lu step %u failed: %s",
                         (unsigned long)repetition, index, chlm_last_error(model));
                return;
            }
        }
        for (uint32_t index = 0; index < golden_vocab; ++index) {
            if (!isfinite(logits[index])) {
                ESP_LOGE(TAG, "non-finite device logit at %lu", (unsigned long)index);
                return;
            }
            float delta = fabsf(logits[index] - expected[index]);
            if (delta > maximum) maximum = delta;
            mean += delta;
        }
    }
    int64_t elapsed = esp_timer_get_time() - started;
    mean /= (float)((size_t)golden_vocab * repetitions);
    const size_t internal_after = heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
    const size_t psram_after = heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
    ESP_LOGI(TAG, "native device golden: %lu sequences max=%g mean=%g",
             (unsigned long)repetitions, maximum, mean);
    ESP_LOGI(TAG, "native timing: %lu tokens in %lld us (%.2f ms/token)",
             (unsigned long)((uint32_t)token_count * repetitions), (long long)elapsed,
             (double)elapsed / ((uint32_t)token_count * repetitions) / 1000.0);
    ESP_LOGI(TAG, "heap internal before=%lu after=%lu; PSRAM before=%lu after=%lu",
             (unsigned long)internal_before, (unsigned long)internal_after,
             (unsigned long)psram_before, (unsigned long)psram_after);
    bool numerical_pass = maximum <= 1e-4f && internal_before == internal_after && psram_before == psram_after;
    const chlm_fact_fields fields = {
        "Transformer", "Magnetically coupled component",
        "moves alternating-current energy between circuits and changes voltage",
        "two coils facing each other, often with core lines between them",
        "changing current in one coil creates a changing magnetic field that induces voltage in the other",
        "a transformer does not make unsafe mains voltage safe by itself"
    };
    const char *prompt =
        "<fact>\nname=Transformer\nfamily=Magnetically coupled component\n"
        "purpose=moves alternating-current energy between circuits and changes voltage\n"
        "symbol=two coils facing each other, often with core lines between them\n"
        "behavior=changing current in one coil creates a changing magnetic field that induces voltage in the other\n"
        "constraint=a transformer does not make unsafe mains voltage safe by itself\n"
        "<ask>\ntask=explain\nquestion=Explain this component simply.\n<answer>\n";
    char answer[384];
    uint32_t generated = 0;
    int64_t generation_started = esp_timer_get_time();
    int generation_result = chlm_generate_grounded(model, tokenizer, prompt, &fields, 64u,
                                                    answer, sizeof(answer), &generated);
    int64_t generation_elapsed = esp_timer_get_time() - generation_started;
    bool grounded_pass = !generation_result && strstr(answer, fields.name) && strstr(answer, fields.purpose);
    ESP_LOGI(TAG, "native grounded answer (%lu tokens, %lld ms): %s",
             (unsigned long)generated, (long long)(generation_elapsed / 1000),
             generation_result ? "GENERATION FAILED" : answer);
    if (numerical_pass && grounded_pass) ESP_LOGI(TAG, "CIRCUITHEROESLM_NATIVE_DEVICE_PASS");
    else ESP_LOGE(TAG, "CIRCUITHEROESLM_NATIVE_DEVICE_FAIL");
}
