# circuitheroesLM native ESR + FactTape v0.3

Research checkpoint trained from random initialization using only the native
implementation on this branch.

| Field | Value |
| --- | ---: |
| Parameters | 573,824 |
| Vocabulary | 1,536 |
| ESR layers | 4 |
| Engineering lanes | 4 |
| Context | 128 |
| Training examples | 2,560 |
| Validation examples | 320 |
| Held-out-family examples | 864 |
| Best validation loss | 0.2801 |
| Held-out verifier | 864/864 |

The test proves bounded task generalization when exact facts are supplied by an
attributed record and resolved through FactTape. It does not prove open-domain
electronics reasoning or correctness of unreviewed source facts.

`model.pt` is the float PyTorch research checkpoint. No ESP32 binary is present
yet because quantization and native C-runtime verification are still open.

