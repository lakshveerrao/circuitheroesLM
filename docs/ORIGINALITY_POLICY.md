# Originality policy

## Non-reuse boundary

The native circuitheroesLM implementation must not copy, translate, port, or
mechanically rewrite source from the earlier prototype or `slvDev/esp32-ai`.
That includes model layers, training loop, quantizer, exporter, binary model
format, host verifier, and ESP32 inference runtime.

The native branch was created directly from repository `main`, whose only file
was the project's MIT license. New implementation files begin on this branch.

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

1. compare native source against the archived prototype and named upstreams;
2. flag matching sequences and manually review every material match;
3. confirm all released weights start from random initialization;
4. publish dataset provenance and model-training manifests;
5. publish the exact quantized-format specification and host/device goldens;
6. retain attribution for data, SDKs, papers, and third-party libraries.

The defensible claim is independently implemented—not that all underlying
mathematics or source engineering facts were invented by this project.

## Published-method attribution

When a published architecture idea is used, its origin must be named even when
the implementation is independent. The per-layer-embedding candidate adapts
Google's published Gemma 3n PLE concept and is documented separately. It uses
no Gemma weights or source code and must not be described as an invention of
circuitheroesLM.
