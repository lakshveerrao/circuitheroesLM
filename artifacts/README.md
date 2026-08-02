# Model artifacts

`model/model.bin` is the locally exported Circuit Heroes LM Circuit Quest pilot v0.2
development artifact. It is 2,124,620 bytes and has SHA-256:

```text
673fc7d7fbd8110e82150a8f4f519b06dddf2d9c97d2d6d9eb33ae880eefcc10
```

This is not an accepted production release. It is limited to the 52-component
hardware information layer described in `pilot/README.md`; the facts still
require independent engineering review, and hardware release gates remain
open. The two earlier broad checkpoints remain rejected because they
hallucinated electronics facts.

The repository is reproducible: dataset preparation, training, quantization,
C inference, hardware configuration, and release packaging are included.
