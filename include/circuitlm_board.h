#pragma once

#include <stddef.h>
#include <stdint.h>

typedef struct {
    const char *name;
    int (*begin)(void *user);
    int (*set_brightness)(void *user, uint8_t percent);
    int (*draw_text)(void *user, const char *utf8);
    int (*draw_frame)(void *user, const uint16_t *rgb565, int width, int height);
    int (*read_touch)(void *user, int *x, int *y, int *pressed);
    void *user;
} circuitlm_display_driver_t;

typedef struct {
    const char *name;
    int (*begin)(void *user);
    int (*record_pcm16)(void *user, int16_t *samples, size_t count, uint32_t rate);
    void *user;
} circuitlm_microphone_driver_t;

typedef struct {
    const char *name;
    int (*begin)(void *user);
    int (*set_volume)(void *user, uint8_t percent);
    int (*play_pcm16)(void *user, const int16_t *samples, size_t count, uint32_t rate);
    void *user;
} circuitlm_speaker_driver_t;

typedef struct {
    const char *board_name;
    uint32_t flash_bytes;
    uint32_t psram_bytes;
    circuitlm_display_driver_t display;
    circuitlm_microphone_driver_t microphone;
    circuitlm_speaker_driver_t speaker;
} circuitlm_board_t;
