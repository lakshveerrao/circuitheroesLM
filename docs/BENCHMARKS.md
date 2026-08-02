# Benchmarks and experiment log

## 2026-08-02: 4.1M electronics memorization experiment — rejected

- Parameters: 4,097,312
- INT4 artifact: 2,124,620 bytes
- Dataset: 103,447 generated tasks from 21,349 KiCad records
- Tokenized training set: 7,996,883 tokens
- Best validation perplexity: approximately 4.17
- C/PyTorch maximum logit difference: 0.00000 (pass)
- Host perplexity sample: 3.70 with FP32 or INT8 activations

Qualitative failures:

- `LM317` was classified as a switching regulator instead of a linear regulator.
- A fuse question produced an unrelated digital-isolator description.

Verdict: the runtime and quantization are correct, but the checkpoint does not
meet factuality requirements. It must not replace the product model or be
advertised as hardware reasoning.

## 2026-08-02: 6.43M grounded higher-compute experiment — rejected

- Parameters: 6,425,856
- Dense core: 1,707,264 parameters
- PLE table: 4,194,304 parameters
- Layers/width: 8 layers, 128 hidden width, 256 FFN width
- Training corpus: 16,725,920 tokens
- Answer tokens: 2,871,821
- Objective: answer-token-only cross entropy with verified facts in context
- Best/final answer-token validation perplexity: 7.68 at step 1,199

The corrected objective removed the misleading reward for predicting prompt
labels, but qualitative generation still failed:

- `LM317_TO-220`, supplied as `Regulator Linear`, produced `Regulator Switching`.
- `Fuse`, with a verified fuse description, produced an unrelated part string.
- A grounded beginner explanation invented a different component and ratings.

Verdict: increasing core capacity and grounding context did not produce an
acceptable generative teacher in this bounded local run. The checkpoint is not
released. Future work requires a high-quality teacher-distillation corpus,
constrained copying/verifier decoding, and an external high-compute training
budget; repeating the same training recipe is not justified.


## Release thresholds

- component/type identification: at least 95%;
- expert-reviewed beginner explanation factuality: at least 90%;
- polarity, pin, unit, and limit rubric: at least 90%;
- unsupported claim rate after verification: below 2%;
- 100-generation ESP32-S3 stability run without crash;
- published flash, SRAM/PSRAM, latency, and tokens/second measurements.
