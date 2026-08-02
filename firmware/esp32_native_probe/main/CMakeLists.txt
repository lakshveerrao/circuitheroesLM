idf_component_register(
    SRCS "main.c" "../../../native_runtime/chlm.c"
         "../../../native_runtime/chlm_tokenizer.c"
         "../../../native_runtime/chlm_generation.c"
    INCLUDE_DIRS "../../../native_runtime"
    EMBED_FILES "golden.bin" "tokenizer.chtk"
    REQUIRES esp_partition esp_timer
)

target_compile_options(${COMPONENT_LIB} PRIVATE -O3)
