# Models and weights

This directory publishes every distinct trained research checkpoint retained
by the project. Duplicate end-of-run and smoke-test files are excluded; the
best checkpoint for each experiment is included.

| Model | Status | PyTorch | ESP32 INT4 |
| --- | --- | ---: | ---: |
| CircuitLM Quest v0.2 | current bounded pilot | 16,414,096 B | 2,124,620 B |
| CircuitLM Pilot v0.1 | historical bounded pilot | 16,414,096 B | 2,124,620 B |
| Grounded answer-loss v1 | rejected: factual failures | 25,736,728 B | not released |
| Memorization v1 | rejected: factual failures | 25,735,936 B | not released |

`*.pt` files contain trainable PyTorch state. `model.bin` is the group-128
ragged-INT4 artifact consumed by the portable C/ESP32 runtime. Quest v0.2 uses
4,097,312 parameters: 558,368 dense-core, 393,216 streamed, and 3,145,728 PLE
table parameters. Architecture: vocabulary 4,096; width 96; 6 layers; 4 heads;
FFN 66; PLE 128; context 256.

The rejected weights are supplied for transparent research reproduction only.
They must not be presented as reliable electronics models. See
[`docs/BENCHMARKS.md`](../docs/BENCHMARKS.md).

Canonical hashes are recorded in [`SHA256SUMS`](SHA256SUMS).
