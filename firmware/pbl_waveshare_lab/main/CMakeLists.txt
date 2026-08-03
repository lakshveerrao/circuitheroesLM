idf_component_register(
    SRCS "main.c"
    INCLUDE_DIRS "."
    REQUIRES esp32_s3_touch_amoled_1_8 lvgl__lvgl espressif__esp_codec_dev esp_psram
)
target_compile_definitions(${COMPONENT_LIB} PRIVATE PBL_TEST_MODE=${PBL_TEST_MODE})
