# Authors

## Creator and project lead

**Laksh** (`lakshveerrao`)

Laksh defined the product vision, offline requirement, electronics teaching
method, device interaction, hardware targets, and acceptance criteria for
Circuit Heroes LM.

## Development assistance

OpenAI Codex assisted with implementation, documentation, testing, dataset
tooling, and model experiments under Laksh's direction.

## Upstream work

The PLE PyTorch model, quantization/export foundation, and portable C inference
runtime were adapted from `slvDev/esp32-ai` under the MIT License. The runtime
header currently retains substantial upstream code and is not a clean-room
rewrite. Per-Layer Embeddings originate in Google Gemma research. KiCad
community contributors created the source component library used to build the
local factual catalogue.

Circuit Heroes does not redistribute slvDev's trained weights and was not
trained on TinyStories. Its electronics corpora, HIL, trained weights, grounded
verifier, game/task design, product firmware integration, and device evaluation
were created for this project under Laksh's direction. See
`docs/ORIGINALITY.md`.
