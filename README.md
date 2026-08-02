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
engineering corpus builder, answer-only training loop, and deterministic tests
are implemented. The first 200-step random-initialized smoke run reduced
validation loss from 7.28 to 4.88. This proves the native path trains; it does
not yet prove useful generation. No production weights are claimed until the
originality, factuality, quantization, and ESP32 release gates pass.

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
