# Circuit Heroes LM

An open-source, electronics-centric TinyLM created by **Laksh** for fully
offline inference on ESP devices.

Circuit Heroes LM combines a compact generative model with a verified local
component catalogue. The catalogue supplies exact names and facts; the model
turns those facts into short beginner explanations, questions, and learning
activities. No cloud API is required after installation.

> Project status: active research preview. The portable runtime and dataset
> pipeline work. The first electronics checkpoint was rejected because it
> hallucinated component facts. It is not presented as a finished model. See
> [docs/BENCHMARKS.md](docs/BENCHMARKS.md).

## Why the factual catalogue matters

A microcontroller model cannot reliably memorize every datasheet. Circuit
Heroes LM therefore uses local retrieval before generation:

```text
question -> local component lookup -> verified fact context -> TinyLM -> verifier -> answer
```

This is still locally generated language, but exact part identity, subtype,
package, polarity, and limits do not depend on guessing.

## Repository contents

- `include/`, `src/`: portable C inference API and INT4 PLE runtime
- `config/`: validated ESP board/display/mic/speaker profiles
- `data/`: 21,349-component KiCad-derived catalogue and manifests
- `tools/`: configuration, dataset, tokenization, and release tools
- `training/`: higher-compute grounded-model training configuration
- `docs/`: architecture, hardware tiers, data, training, and release policy
- `artifacts/`: accepted release artifacts only (currently empty by policy)

## Quick start

Generate a hardware configuration:

```sh
python3 tools/configure.py \
  --board waveshare-s3-touch-amoled-1.8 \
  --mic modulino-i2s \
  --speaker mini-i2s \
  --output generated/circuitlm_config.h
```

Prepare the grounded instruction corpus:

```sh
python3 tools/prepare_dataset.py \
  --catalogue data/electronics_catalogue.tsv \
  --output generated/dataset
python3 tools/tokenize_dataset.py \
  --dataset generated/dataset \
  --tokenizer model-tokenizer.json \
  --output generated/tokens
```

Build a deterministic downloadable bundle after producing an accepted model.
No weight bundle is currently published because both experimental checkpoints
failed qualitative factuality tests:

```sh
python3 tools/package_release.py \
  --model path/to/model-int4.bin \
  --tokenizer model-tokenizer.json \
  --catalogue data/electronics-pack.bin \
  --output dist/Circuit-Heroes-LM.zip
```

## Supported hardware

The full reference target is the Waveshare ESP32-S3 Touch AMOLED 1.8 with 16
MiB flash and 8 MiB PSRAM. ESP32-S3/P4, S2, C3, and C6 profiles use the same API
but different model tiers. A C3 without PSRAM cannot run the same checkpoint as
an S3 with 8 MiB PSRAM; the configuration tool rejects impossible combinations.

## Authorship and attribution

Circuit Heroes LM was created by **Laksh**. Development assistance and code
generation were provided through OpenAI Codex. The PLE reference inference work
is adapted from `slvDev/esp32-ai` under its MIT license. The electronics
catalogue is derived from the KiCad official symbol library under CC BY-SA 4.0
with the KiCad library exception. See [AUTHORS.md](AUTHORS.md) and `licenses/`.

## License

New project code is Apache-2.0. Third-party runtime code retains MIT terms.
KiCad-derived catalogue data remains CC BY-SA 4.0 with its exception. Model
weights will state their license in each release model card.
