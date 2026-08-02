#define CIRCUITLM_BOARD CIRCUITLM_BOARD_WAVESHARE_S3_TOUCH_AMOLED_18
#define CIRCUITLM_DISPLAY CIRCUITLM_DISPLAY_AMOLED_18_TOUCH
#define CIRCUITLM_MIC CIRCUITLM_MIC_MODULINO
#define CIRCUITLM_SPEAKER CIRCUITLM_SPEAKER_MINI_I2S
#include "circuitlm_config_base.h"

// Hardware setup belongs in a board adapter. CircuitLM itself receives token
// IDs and returns decoded tokens, so this application can replace the display,
// microphone, and speaker without modifying the model runtime.
void app_main(void)
{
    // circuitlm_init(&model_source, &allocator);
    // circuitlm_generate(&request, on_token, NULL);
}
