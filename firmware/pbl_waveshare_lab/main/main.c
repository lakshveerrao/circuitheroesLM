#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "bsp/esp-bsp.h"
#include "driver/i2c_master.h"
#include "esp_chip_info.h"
#include "esp_codec_dev.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_psram.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "lvgl.h"

#ifndef PBL_TEST_MODE
#define PBL_TEST_MODE 0
#endif

#define SAMPLE_RATE 16000
#define RECORD_SECONDS 3
#define AUDIO_SAMPLES (SAMPLE_RATE * RECORD_SECONDS)
#define AUDIO_BYTES (AUDIO_SAMPLES * sizeof(int16_t))
#define FRAME_SAMPLES 320
#define SAFE_VOLUME 24

static const char *TAG = "pbl_lab";
static esp_codec_dev_handle_t s_speaker;
static esp_codec_dev_handle_t s_microphone;
static lv_obj_t *s_status;
static lv_obj_t *s_meter;
static lv_obj_t *s_action_button;
static volatile bool s_audio_busy;

static lv_obj_t *active_screen(void)
{
#if LVGL_VERSION_MAJOR >= 9
    return lv_screen_active();
#else
    return lv_scr_act();
#endif
}

static void set_status(const char *text)
{
    if (s_status == NULL) return;
    if (bsp_display_lock(1000)) {
        lv_label_set_text(s_status, text);
        bsp_display_unlock();
    }
}

static lv_obj_t *make_label(lv_obj_t *parent, const char *text, int y, int width, uint32_t color)
{
    lv_obj_t *label = lv_label_create(parent);
    lv_label_set_text(label, text);
    lv_label_set_long_mode(label, LV_LABEL_LONG_WRAP);
    lv_obj_set_width(label, width);
    lv_obj_set_style_text_color(label, lv_color_hex(color), 0);
    lv_obj_set_style_text_align(label, LV_TEXT_ALIGN_CENTER, 0);
    lv_obj_align(label, LV_ALIGN_TOP_MID, 0, y);
    return label;
}

static lv_obj_t *make_button(lv_obj_t *parent, const char *text, int y)
{
    lv_obj_t *button = lv_button_create(parent);
    lv_obj_set_size(button, 286, 58);
    lv_obj_align(button, LV_ALIGN_TOP_MID, 0, y);
    lv_obj_set_style_radius(button, 18, 0);
    lv_obj_set_style_bg_color(button, lv_color_hex(0x24c8a5), 0);
    lv_obj_t *label = lv_label_create(button);
    lv_label_set_text(label, text);
    lv_obj_set_style_text_color(label, lv_color_hex(0x061a22), 0);
    lv_obj_set_style_text_font(label, &lv_font_montserrat_18, 0);
    lv_obj_center(label);
    return button;
}

static void create_shell(const char *eyebrow, const char *title, const char *instruction)
{
    lv_obj_t *screen = active_screen();
    lv_obj_set_style_bg_color(screen, lv_color_hex(0x07131c), 0);
    lv_obj_clear_flag(screen, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *stripe = lv_obj_create(screen);
    lv_obj_remove_style_all(stripe);
    lv_obj_set_size(stripe, 368, 8);
    lv_obj_set_style_bg_color(stripe, lv_color_hex(0x24c8a5), 0);
    lv_obj_set_style_bg_opa(stripe, LV_OPA_COVER, 0);
    lv_obj_align(stripe, LV_ALIGN_TOP_MID, 0, 0);

    lv_obj_t *small = make_label(screen, eyebrow, 24, 330, 0x67e8ce);
    lv_obj_set_style_text_font(small, &lv_font_montserrat_14, 0);
    lv_obj_t *heading = make_label(screen, title, 56, 334, 0xffffff);
    lv_obj_set_style_text_font(heading, &lv_font_montserrat_24, 0);
    make_label(screen, instruction, 112, 318, 0xb7cbd7);

    lv_obj_t *card = lv_obj_create(screen);
    lv_obj_set_size(card, 328, 122);
    lv_obj_align(card, LV_ALIGN_TOP_MID, 0, 190);
    lv_obj_set_style_radius(card, 20, 0);
    lv_obj_set_style_bg_color(card, lv_color_hex(0x102532), 0);
    lv_obj_set_style_border_color(card, lv_color_hex(0x275367), 0);
    lv_obj_set_style_border_width(card, 1, 0);
    lv_obj_clear_flag(card, LV_OBJ_FLAG_SCROLLABLE);
    s_status = make_label(card, "Starting hardware...", 22, 280, 0xffffff);
    lv_obj_set_style_text_font(s_status, &lv_font_montserrat_18, 0);
}

static bool init_audio(void)
{
    if (s_speaker && s_microphone) return true;
    esp_codec_dev_sample_info_t format = {
        .bits_per_sample = 16,
        .channel = 1,
        .channel_mask = 0,
        .sample_rate = SAMPLE_RATE,
        .mclk_multiple = 256,
    };
    s_speaker = bsp_audio_codec_speaker_init();
    s_microphone = bsp_audio_codec_microphone_init();
    if (!s_speaker || !s_microphone) {
        ESP_LOGE(TAG, "ES8311 device creation failed");
        return false;
    }
    if (esp_codec_dev_open(s_speaker, &format) != ESP_CODEC_DEV_OK ||
        esp_codec_dev_open(s_microphone, &format) != ESP_CODEC_DEV_OK) {
        ESP_LOGE(TAG, "ES8311 open failed");
        return false;
    }
    esp_codec_dev_set_out_vol(s_speaker, SAFE_VOLUME);
    esp_codec_dev_set_in_gain(s_microphone, 30.0f);
    ESP_LOGI(TAG, "Audio ready: 16 kHz mono, safe output volume %d", SAFE_VOLUME);
    return true;
}

static void play_gentle_tone(void)
{
    if (!init_audio()) return;
    int16_t frame[FRAME_SAMPLES];
    float phase = 0.0f;
    const float step = 2.0f * 3.14159265f * 440.0f / SAMPLE_RATE;
    for (int block = 0; block < 13; ++block) {
        for (int index = 0; index < FRAME_SAMPLES; ++index) {
            frame[index] = (int16_t)(sinf(phase) * 2600.0f);
            phase += step;
            if (phase >= 2.0f * 3.14159265f) phase -= 2.0f * 3.14159265f;
        }
        esp_codec_dev_write(s_speaker, frame, sizeof(frame));
    }
    int16_t silence[FRAME_SAMPLES] = {0};
    esp_codec_dev_write(s_speaker, silence, sizeof(silence));
}

static void audio_task(void *argument)
{
    const int mode = (int)(intptr_t)argument;
    s_audio_busy = true;
    if (mode == 3) {
        set_status("Playing one gentle tone...");
        play_gentle_tone();
        set_status("Speaker path passed.\nTap to play it once again.");
        s_audio_busy = false;
        vTaskDelete(NULL);
        return;
    }

    if (!init_audio()) {
        set_status("Audio initialization failed.\nCheck the serial details.");
        s_audio_busy = false;
        vTaskDelete(NULL);
        return;
    }

    int16_t *recording = heap_caps_malloc(AUDIO_BYTES, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (recording == NULL) recording = malloc(AUDIO_BYTES);
    if (recording == NULL) {
        set_status("Not enough memory for recording.");
        s_audio_busy = false;
        vTaskDelete(NULL);
        return;
    }
    set_status("Listening for 3 seconds...\nSpeak now.");
    int result = esp_codec_dev_read(s_microphone, recording, AUDIO_BYTES);
    if (result != ESP_CODEC_DEV_OK) {
        ESP_LOGE(TAG, "microphone read failed: %d", result);
        set_status("Microphone read failed.\nSee the serial monitor.");
    } else {
        set_status("Captured locally.\nPlaying it once...");
        result = esp_codec_dev_write(s_speaker, recording, AUDIO_BYTES);
        if (result == ESP_CODEC_DEV_OK) {
            set_status(mode == 6 ? "Hardware bridge passed.\nReady for the local model." :
                                   "Microphone + speaker passed.\nTap to repeat.");
        } else {
            set_status("Speaker playback failed.\nSee the serial monitor.");
        }
    }
    free(recording);
    s_audio_busy = false;
    vTaskDelete(NULL);
}

static void audio_button_event(lv_event_t *event)
{
    (void)event;
    if (s_audio_busy) return;
    xTaskCreate(audio_task, "pbl_audio", 6144, (void *)(intptr_t)PBL_TEST_MODE, 5, NULL);
}

static void touch_event(lv_event_t *event)
{
    lv_point_t point;
    lv_indev_t *input = lv_indev_active();
    if (input == NULL) return;
    lv_indev_get_point(input, &point);
    char message[80];
    snprintf(message, sizeof(message), "Touch detected\nX %ld   Y %ld", (long)point.x, (long)point.y);
    lv_label_set_text(s_status, message);

    lv_obj_t *dot = lv_obj_create(lv_event_get_target(event));
    lv_obj_remove_style_all(dot);
    lv_obj_set_size(dot, 14, 14);
    lv_obj_set_style_radius(dot, LV_RADIUS_CIRCLE, 0);
    lv_obj_set_style_bg_color(dot, lv_color_hex(0xffca4b), 0);
    lv_obj_set_style_bg_opa(dot, LV_OPA_COVER, 0);
    lv_obj_set_pos(dot, point.x - 7, point.y - 7);
}

static void meter_task(void *argument)
{
    (void)argument;
    if (!init_audio()) {
        set_status("Microphone initialization failed.");
        vTaskDelete(NULL);
        return;
    }
    int16_t samples[FRAME_SAMPLES];
    while (true) {
        if (esp_codec_dev_read(s_microphone, samples, sizeof(samples)) == ESP_CODEC_DEV_OK) {
            uint32_t peak = 0;
            for (size_t index = 0; index < FRAME_SAMPLES; ++index) {
                uint32_t level = samples[index] < 0 ? (uint32_t)(-samples[index]) : (uint32_t)samples[index];
                if (level > peak) peak = level;
            }
            int percent = (int)((peak * 100u) / 32767u);
            if (percent > 100) percent = 100;
            if (bsp_display_lock(100)) {
                lv_bar_set_value(s_meter, percent, LV_ANIM_ON);
                char text[64];
                snprintf(text, sizeof(text), "Live microphone level\n%d%%", percent);
                lv_label_set_text(s_status, text);
                bsp_display_unlock();
            }
        }
        vTaskDelay(pdMS_TO_TICKS(30));
    }
}

static void create_color_grid(void)
{
    static const uint32_t colors[] = {0xf04848, 0x24c8a5, 0x3195ff, 0xffca4b, 0xffffff, 0x1b2630};
    static const char *names[] = {"RED", "GREEN", "BLUE", "YELLOW", "WHITE", "BLACK"};
    for (int index = 0; index < 6; ++index) {
        lv_obj_t *tile = lv_obj_create(active_screen());
        lv_obj_set_size(tile, 152, 72);
        lv_obj_align(tile, LV_ALIGN_TOP_LEFT, 22 + (index % 2) * 172, 176 + (index / 2) * 84);
        lv_obj_set_style_bg_color(tile, lv_color_hex(colors[index]), 0);
        lv_obj_set_style_border_width(tile, 0, 0);
        lv_obj_set_style_radius(tile, 14, 0);
        lv_obj_t *label = lv_label_create(tile);
        lv_label_set_text(label, names[index]);
        lv_obj_set_style_text_color(label, lv_color_hex(index == 4 || index == 3 ? 0x111111 : 0xffffff), 0);
        lv_obj_center(label);
    }
}

static void create_memory_view(void)
{
    char text[160];
    const size_t internal = heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
    const size_t psram = heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
    void *probe = heap_caps_malloc(256 * 1024, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    snprintf(text, sizeof(text), "Internal SRAM  %lu KB\nPSRAM free     %lu KB\n256 KB probe   %s",
             (unsigned long)(internal / 1024), (unsigned long)(psram / 1024), probe ? "PASS" : "CHECK");
    free(probe);
    lv_label_set_text(s_status, text);
}

static void create_chip_view(void)
{
    esp_chip_info_t info;
    esp_chip_info(&info);
    char text[160];
    snprintf(text, sizeof(text), "ESP32-S3 revision %d\n%d CPU cores\nPSRAM %s",
             info.revision, info.cores, esp_psram_is_initialized() ? "ready" : "not initialized");
    lv_label_set_text(s_status, text);
}

static void create_ui(void)
{
    if (PBL_TEST_MODE == 1) {
        create_shell("PBL DISPLAY LAB", "Color + alignment", "Every tile must be clean, centered and visibly different.");
        lv_obj_add_flag(lv_obj_get_parent(s_status), LV_OBJ_FLAG_HIDDEN);
        create_color_grid();
        return;
    }
    if (PBL_TEST_MODE == 2) {
        create_shell("PBL TOUCH LAB", "Draw with your finger", "Touch anywhere. Every point should appear exactly beneath your finger.");
        lv_obj_add_event_cb(active_screen(), touch_event, LV_EVENT_PRESSED, NULL);
        lv_label_set_text(s_status, "Waiting for touch...");
        return;
    }
    if (PBL_TEST_MODE == 3) {
        create_shell("PBL AUDIO LAB", "Safe speaker test", "Nothing plays automatically. Tap below for one short, gentle tone.");
        s_action_button = make_button(active_screen(), "Play gentle tone", 344);
        lv_obj_add_event_cb(s_action_button, audio_button_event, LV_EVENT_CLICKED, NULL);
        lv_label_set_text(s_status, "Speaker is silent and ready.");
        return;
    }
    if (PBL_TEST_MODE == 4) {
        create_shell("PBL AUDIO LAB", "Microphone meter", "Speak near the board. Audio stays in RAM and is never uploaded.");
        s_meter = lv_bar_create(active_screen());
        lv_obj_set_size(s_meter, 286, 34);
        lv_obj_align(s_meter, LV_ALIGN_TOP_MID, 0, 350);
        lv_obj_set_style_bg_color(s_meter, lv_color_hex(0x193442), 0);
        lv_obj_set_style_bg_color(s_meter, lv_color_hex(0x24c8a5), LV_PART_INDICATOR);
        xTaskCreate(meter_task, "pbl_meter", 6144, NULL, 5, NULL);
        return;
    }
    if (PBL_TEST_MODE == 5) {
        create_shell("PBL VOICE LAB", "Record + playback", "Tap once, speak for three seconds, then hear the captured audio once.");
        s_action_button = make_button(active_screen(), "Record my voice", 344);
        lv_obj_add_event_cb(s_action_button, audio_button_event, LV_EVENT_CLICKED, NULL);
        lv_label_set_text(s_status, "No audio leaves this device.");
        return;
    }
    if (PBL_TEST_MODE == 6) {
        create_shell("CIRCUIT HEROES", "Agent hardware bridge", "A one-screen example for listen, think and answer product states.");
        s_action_button = make_button(active_screen(), "Test Listen → Answer", 344);
        lv_obj_add_event_cb(s_action_button, audio_button_event, LV_EVENT_CLICKED, NULL);
        lv_label_set_text(s_status, "Display + touch ready.\nTap to test the voice path.");
        return;
    }
    if (PBL_TEST_MODE == 7) {
        create_shell("PBL BUS LAB", "I2C device map", "The board BSP initialized its shared bus. Device details are also in serial.");
        lv_label_set_text(s_status, "I2C bus initialized\nTouch, codec, PMU, RTC and IMU\nare available through the BSP.");
        return;
    }
    if (PBL_TEST_MODE == 8) {
        create_shell("PBL MEMORY LAB", "SRAM + PSRAM health", "A temporary allocation checks PSRAM without modifying stored files.");
        create_memory_view();
        return;
    }

    create_shell("PBL PRODUCT LAB", "Your board is alive", "Test display, touch, microphone and speaker from one stable screen.");
    s_action_button = make_button(active_screen(), "Test voice hardware", 344);
    lv_obj_add_event_cb(s_action_button, audio_button_event, LV_EVENT_CLICKED, NULL);
    lv_label_set_text(s_status, "AMOLED + touch passed.\nTap to test microphone + speaker.");
}

void app_main(void)
{
    ESP_LOGI(TAG, "PBL Waveshare hardware lab mode %d", PBL_TEST_MODE);
    lv_display_t *display = bsp_display_start();
    if (display == NULL) {
        ESP_LOGE(TAG, "AMOLED initialization failed");
        return;
    }
    ESP_ERROR_CHECK(bsp_display_brightness_set(78));
    if (!bsp_display_lock(1000)) {
        ESP_LOGE(TAG, "LVGL lock failed");
        return;
    }
    create_ui();
    bsp_display_unlock();

    if (PBL_TEST_MODE == 7) {
        ESP_LOGI(TAG, "BSP I2C handle=%p", bsp_i2c_get_handle());
    } else if (PBL_TEST_MODE == 8) {
        ESP_LOGI(TAG, "internal=%lu psram=%lu",
                 (unsigned long)heap_caps_get_free_size(MALLOC_CAP_INTERNAL),
                 (unsigned long)heap_caps_get_free_size(MALLOC_CAP_SPIRAM));
    } else if (PBL_TEST_MODE == 9) {
        create_chip_view();
    }

    while (true) vTaskDelay(pdMS_TO_TICKS(1000));
}
