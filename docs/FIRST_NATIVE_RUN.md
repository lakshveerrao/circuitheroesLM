# First native training run

Run: `native-esr-v0.1`, seed `20260802`, CPU, 200 steps, batch 8.

| Metric | Value |
| --- | ---: |
| Random initialization | yes |
| Parameters | 523,120 |
| Initial validation loss | 7.2838 |
| Step-200 validation loss | 4.8756 |
| Wall time | 49.0 seconds |

The monotonic validation improvement establishes that the independently
implemented ESR model, tokenizer, engineering corpus and answer-only objective
form a working training path. It is not a model-quality release. Generation,
held-out-family factuality, quantization and ESP32 inference remain open gates.

## 800-step candidate verdict

The longer run reached best validation loss 3.542 at step 575, then overfit.
A 12-example validation generation sample and a 12-example held-out-family
sample both scored 0/12. Outputs were fluent but substituted memorized training
components for the supplied fact card. The checkpoint is rejected.

This failure blocks export, quantization, and ESP32 integration. The next
candidate requires a larger paraphrased engineering corpus and an architecture
or objective with demonstrably stronger fact-card conditioning/copy behavior.
