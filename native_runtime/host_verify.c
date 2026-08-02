#include "chlm.h"

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void *read_file(const char *path, size_t *length) {
    FILE *file=fopen(path,"rb"); if(!file)return NULL; fseek(file,0,SEEK_END); long size=ftell(file); rewind(file);
    void *data=malloc((size_t)size); if(!data||fread(data,1,(size_t)size,file)!=(size_t)size){free(data);fclose(file);return NULL;}
    fclose(file);*length=(size_t)size;return data;
}

int main(int argc,char **argv){
    if(argc!=3){fprintf(stderr,"usage: %s model.chlm model.chlm.golden.bin\n",argv[0]);return 2;}
    size_t model_bytes=0,golden_bytes=0; uint8_t *image=read_file(argv[1],&model_bytes),*golden=read_file(argv[2],&golden_bytes);
    if(!image||!golden||golden_bytes<12||memcmp(golden,"CHLG",4)){fprintf(stderr,"file read/header failure\n");return 2;}
    uint16_t version=0,count=0;uint32_t vocab=0;memcpy(&version,golden+4,2);memcpy(&count,golden+6,2);memcpy(&vocab,golden+8,4);
    if(version!=1||golden_bytes!=12u+(size_t)count*4u+(size_t)vocab*4u){fprintf(stderr,"golden size failure\n");return 2;}
    chlm_model *model=NULL;if(chlm_create(&model,image,model_bytes)){fprintf(stderr,"model load: %s\n",chlm_last_error(model));chlm_destroy(model);return 1;}
    float *logits=(float *)malloc((size_t)vocab*sizeof(float));uint32_t *tokens=(uint32_t *)(golden+12);
    for(uint16_t i=0;i<count;++i)if(chlm_step(model,tokens[i],logits,vocab)){fprintf(stderr,"step failure at %u: %s\n",i,chlm_last_error(model));return 1;}
    const float *expected=(const float *)(golden+12u+(size_t)count*4u);float maximum=0.0f,mean=0.0f;
    for(uint32_t i=0;i<vocab;++i){if(!isfinite(logits[i])||!isfinite(expected[i])){fprintf(stderr,"non-finite verification value at %u\n",i);return 1;}float delta=fabsf(logits[i]-expected[i]);if(delta>maximum)maximum=delta;mean+=delta;}
    mean/=(float)vocab;printf("circuitheroesLM CHLM verify: max=%g mean=%g vocab=%u tokens=%u\n",maximum,mean,vocab,count);
    free(logits);chlm_destroy(model);free(image);free(golden);return maximum<=1e-4f?0:1;
}
