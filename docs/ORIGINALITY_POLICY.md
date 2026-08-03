# Originality policy

## Implementation provenance

circuitheroesLM develops and publishes its model layers, training loop,
quantizer, exporter, binary model format, host verifier, and ESP32 inference
runtime as one coherent embedded-AI stack. Release manifests identify the
training seed, corpus, configuration, weights, and checksums used for each
candidate.

## What may be used

- properly attributed engineering facts and datasets;
- public mathematical knowledge and papers;
- standard libraries such as PyTorch during training;
- independently written implementations of documented algorithms;
- hardware vendor SDKs and board-support packages under their licenses.

Using a known mathematical operation is not the same as claiming it was
invented here. Any future novelty claim requires a documented prior-art review.

## Audit gates

Before release:

1. review source provenance before release;
2. confirm all released weights start from their declared initialization;
3. publish dataset provenance and model-training manifests;
4. publish the exact quantized-format specification and host/device goldens;
5. retain attribution for data, SDKs, papers, and third-party libraries;
6. attach measured evidence to every performance claim.

The defensible novelty claim is the circuitheroesLM system design and its
measured embedded implementation—not ownership of established mathematics or
source engineering facts.

## Published-method attribution

When a published architecture idea is used, its origin is named. The
per-layer-embedding candidate adapts Google's published Gemma 3n PLE concept to
the ESR architecture and a microcontroller flash-streaming path; the adaptation
is documented separately.
