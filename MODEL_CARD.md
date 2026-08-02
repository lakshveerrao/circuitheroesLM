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

## Current pilot

The `ple-quest-v0_2-s84` development checkpoint is a bounded demonstration:

- 52 components from `pilot/hil_v0_1.json`;
- four tasks per component: explanation, symbol, behavior, and mystery-game clue;
- 4,097,312 parameters and a 2,124,620-byte INT4 artifact;
- 208/208 canonical greedy generations passed the deterministic verifier;
- local retrieval, generated response verification, and grounded fallback are
  required parts of the runtime.

That result measures the exact 52-component prompt contract. It is not an
unseen-component benchmark, an expert factuality review, or proof of general
hardware reasoning. The fact file is marked `engineering-review-required`.

## Current limitation

The pilot proves local, constrained generation for its fixed hardware
information layer. It does not prove broad electronics reasoning and is not an
accepted production model. Both earlier broad electronics experiments were
rejected after qualitative hallucination tests. Visible product answers must
remain catalogue-grounded until a future checkpoint passes every release gate
below.

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
