#include "chlm.h"
#include "chlm_generation.h"
#include "chlm_tokenizer.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned char *read_file(const char *path, size_t *bytes) {
    FILE *file = fopen(path, "rb");
    if (!file) return NULL;
    if (fseek(file, 0, SEEK_END) || (*bytes = (size_t)ftell(file)) == 0 || fseek(file, 0, SEEK_SET)) {
        fclose(file); return NULL;
    }
    unsigned char *data = (unsigned char *)malloc(*bytes);
    if (!data || fread(data, 1, *bytes, file) != *bytes) { free(data); data = NULL; }
    fclose(file);
    return data;
}

int main(int argc, char **argv) {
    if (argc != 3) { fprintf(stderr, "usage: %s model.chlm tokenizer.chtk\n", argv[0]); return 2; }
    size_t model_bytes = 0, tokenizer_bytes = 0;
    unsigned char *model_image = read_file(argv[1], &model_bytes);
    unsigned char *tokenizer_image = read_file(argv[2], &tokenizer_bytes);
    chlm_model *model = NULL;
    chlm_tokenizer *tokenizer = NULL;
    if (!model_image || !tokenizer_image || chlm_create(&model, model_image, model_bytes) ||
        chlm_tokenizer_create(&tokenizer, tokenizer_image, tokenizer_bytes)) {
        fprintf(stderr, "native model/tokenizer load failed\n"); return 1;
    }
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
    int result = chlm_generate_grounded(model, tokenizer, prompt, &fields, 64u,
                                        answer, sizeof(answer), &generated);
    printf("circuitheroesLM grounded generation (%lu tokens): %s\n",
           (unsigned long)generated, result ? "FAILED" : answer);
    int valid = !result && strstr(answer, fields.name) && strstr(answer, fields.purpose);
    chlm_tokenizer_destroy(tokenizer); chlm_destroy(model);
    free(tokenizer_image); free(model_image);
    return valid ? 0 : 1;
}
