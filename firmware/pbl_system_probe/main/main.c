#include <stdint.h>

#include "esp_chip_info.h"
#include "esp_flash.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_system.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "pbl_system";

void app_main(void)
{
    esp_chip_info_t chip;
    uint32_t flash_bytes = 0;
    esp_chip_info(&chip);
    esp_flash_get_size(NULL, &flash_bytes);

    ESP_LOGI(TAG, "PBL system probe ready");
    ESP_LOGI(TAG, "chip model=%d revision=%d cores=%d features=0x%08lx",
             chip.model, chip.revision, chip.cores, (unsigned long)chip.features);
    ESP_LOGI(TAG, "flash=%lu bytes internal_heap=%lu bytes psram=%lu bytes",
             (unsigned long)flash_bytes,
             (unsigned long)heap_caps_get_free_size(MALLOC_CAP_INTERNAL),
             (unsigned long)heap_caps_get_free_size(MALLOC_CAP_SPIRAM));

    uint32_t heartbeat = 0;
    while (true) {
        ESP_LOGI(TAG, "heartbeat %lu | free heap %lu bytes",
                 (unsigned long)heartbeat++, (unsigned long)esp_get_free_heap_size());
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
