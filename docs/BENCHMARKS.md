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

## 2026-08-02: bounded 52-component ESP32 pilot — development pass

- Parameters: 4,097,312
- INT4 artifact: 2,124,620 bytes
- Hardware information layer: 52 components, three tasks per component
- Training: 1,800 steps, 7,372,800 tokens seen
- Final validation loss/perplexity: 0.0692 / 1.0717
- Canonical greedy checks: 156/156 passed
- Artifact SHA-256:
  `3e6b1f227a8d09d2ddcf0c4f48b6fd28d5cbf1be165125f3452d62415338a9da`
- ESP-IDF 5.5.1 firmware compile: pass; application size 1,080,320 bytes
- ESP32-S3 N16R8 device boot and model initialization: pass
- Tantalum-capacitor device generation: pass; verifier accepted the exact
  one-sentence answer
- Device timing for that 172-token prompt and 24-token answer: 19,274 ms prompt
  processing, 3,110 ms generation, 22,384 ms total (7.72 generated tokens/s)

Verdict: suitable for an explicitly labelled, catalogue-grounded pilot. The
test covers the canonical prompts for the same 52 records used to construct
the training corpus. It is not evidence of unseen-component generalization,
expert-reviewed factuality, or a broad electronics foundation model. Device
stability and full hardware audio/UI validation remain open release gates. A
warm-reset test exposed intermittent FT5x06 discovery. The firmware now allows
a three-second recovery window, and the subsequent device warm-reset test found
the controller at 980 ms. A longer repeated-reset stress test is still required
before release.

## 2026-08-02: Circuit Quest v0.2 on-device pass

- Hardware information layer: 52 components, four tasks per component
- Canonical greedy checks: 208/208 passed, including non-revealing game clues
- Artifact SHA-256:
  `673fc7d7fbd8110e82150a8f4f519b06dddf2d9c97d2d6d9eb33ae880eefcc10`
- ESP32-S3 generated mission: “choose the part that provides stable
  capacitance in a small package”
- Device timing: 104 prompt tokens in 11,051 ms; 28 generated tokens in
  3,235 ms; 14,286 ms total (8.66 generated tokens/s)
- Firmware, model, 8,000-record catalogue, and 86-clip voice pack flash
  regions all passed byte-for-byte verification

Verdict: the new game task works locally and passes its grounded verifier on
the target device. Circuit Quest shows an immediate verified clue while the
live model generates, then swaps in the accepted AI mission. This remains a
bounded 52-component pilot, not evidence of open-domain hardware reasoning.
