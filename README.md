# circuitheroesLM

**circuitheroesLM is a native, electronics-centric language model designed for
fully offline inference on ESP32-class microcontrollers.**

This branch starts from the repository's original one-file `main` history. It
does not contain or import the earlier slvDev-based prototype runtime, model,
exporter, tokenizer, model format, or weights.

## What it is

circuitheroesLM is trained to model engineering language and relationships:
components, subtypes, symbols, pins, units, connections, topology, behavior,
constraints, failure modes, explanations, questions, and game missions. It is
not initialized from TinyStories or another pretrained language model.

The native architecture is the **Engineering State Router (ESR)**: an
attention-free recurrent decoder with four persistent engineering state lanes
and a compact gated channel mixer. Retrieved fact cards provide attributed
engineering knowledge; the learned model turns grounded records into language.

## Current status

The architecture specification, native tokenizer, host reference model,
Engineering FactTape, corpus builder, answer-only training loop, generation
evaluator, and deterministic tests are implemented. Candidate v0.3 passed all
864 held-out-family checks across six tasks. Float weights and the exact
tokenizer are published as a research checkpoint. Quantized and ESP32 release
status remains blocked until native export, C numerical goldens and device
stability gates pass.

Read [`docs/NATIVE_ARCHITECTURE.md`](docs/NATIVE_ARCHITECTURE.md) and
[`docs/ORIGINALITY_POLICY.md`](docs/ORIGINALITY_POLICY.md) before making claims
about the project.

## Name

The product and model name is exactly **circuitheroesLM**. Lowercase package
identifiers use `circuitheroeslm` only where tooling requires it.

## License

Project implementation: MIT. Attributed datasets keep their own licenses and
notices. Established mathematical ideas are cited; the project does not claim
to have invented recurrent networks, tokenization, quantization, or language
modelling as general concepts.
