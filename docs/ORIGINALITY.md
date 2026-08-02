# Originality and upstream boundary

This page states exactly what Circuit Heroes LM created and what it adapted.
It is intentionally more precise than marketing language.

## Source audit

On 2026-08-02, the published `slvDev/esp32-ai` repository was compared against
this repository:

- `include/circuitlm_ple_runtime.h` was byte-for-byte identical to upstream
  `firmware/common/llm.h` at the audited revision;
- `training/model.py` differed from upstream `src/model.py` only in its project
  docstring/attribution header;
- `training/export.py` retained the upstream binary format, group-128 ragged
  INT4 packing, FP16 scales, and golden-verification method;
- related training, sampling, and quantization code began from the same MIT
  reference implementation and was extended for Circuit Heroes experiments.

Therefore Circuit Heroes must retain the upstream MIT notice. It would be
incorrect to describe the underlying PLE runtime as wholly invented here.

## Circuit Heroes original work

| Area | Circuit Heroes contribution |
| --- | --- |
| Domain | Electronics/component learning rather than TinyStories prose |
| Data | KiCad-derived 21,349-record catalogue, generated grounded corpora, and 52-record reviewed pilot HIL |
| Tasks | Explanation, symbol, behavior, and non-revealing live-game clue contracts |
| Weights | Independently trained CircuitLM Pilot v0.1 and Quest v0.2 checkpoints; no slvDev weights reused |
| Safety | Local factual-overlap, identity, uncertainty, and answer-reveal verifier with deterministic fallback |
| Product | Circuit Heroes ESP32-S3 firmware, catalogue retrieval, AMOLED/touch UI, offline voice flow, progress, and Circuit Quest engine |
| Evaluation | 208/208 bounded canonical checks, device flash verification, and measured on-chip generation |

## Correct one-sentence description

> Circuit Heroes LM is an electronics-specialized, independently trained model
> and offline ESP32-S3 learning product built on the MIT-licensed PLE reference
> architecture and inference implementation from slvDev/esp32-ai.

This is a meaningful new model, dataset, verifier, and product application. It
is not a claim that every underlying transformer or inference primitive was
invented by this project.
