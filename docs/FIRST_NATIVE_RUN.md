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
