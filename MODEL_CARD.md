# Circuit Heroes LM developer checkpoint model card

## Baseline compatibility profile

- Repository version: `0.1.0-dev`
- Creator: Laksh
- Accepted release weights: none
- Intended target: ESP32-S3 with 16 MiB flash and 8 MiB PSRAM
- Offline: yes after model bundle installation
- Baseline parameters: 4,097,312
- Weight format: group-wise INT4 with FP16 scales
- Vocabulary: 4,096 tokens
- Architecture: 6-layer decoder, 96 hidden width, 4 heads, PLE width 128
- Context limit: 256 tokens
- Baseline artifact size: 2,124,620 bytes

## Intended use

Short, beginner-friendly electronics explanations and constrained educational
games. The model must be paired with the factual electronics catalogue and an
answer verifier. It is not suitable for safety-critical circuit design,
mains-voltage advice, medical hardware, or unsupervised component selection.

## Current limitation

The baseline checkpoint predates the grounded training pipeline. It proves
local inference but does not prove broad electronics reasoning and is not
published as an accepted model. Both custom electronics experiments were
rejected after qualitative hallucination tests.
Visible product answers must remain catalogue-grounded until a new checkpoint
passes every release gate below.

## CircuitLM 1.0 release gates

1. Exact component/type identification: at least 95% on a held-out, family-split set.
2. Beginner explanation factuality: at least 90% expert-reviewed pass rate.
3. Polarity, pin, unit, and limit questions: at least 90% exact-match or rubric pass.
4. Hallucinated part/type rate: below 2% after verifier intervention.
5. ESP32-S3 cold boot, 100 generations, audio playback, and UI stress test without crash.
6. Publish flash size, peak SRAM/PSRAM, first-token latency, and tokens/second.
7. Verify zero network dependency in firmware and demonstration setup.

The phrase “world's first” must not appear in a release until a documented
novelty search and reproducible public demonstration are complete.
