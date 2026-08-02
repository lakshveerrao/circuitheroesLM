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

`model.pt` is the float PyTorch research checkpoint. `model.chlm` is the native
614,848-byte row-INT8 reference export. INT8 retained 864/864 held-out verifier
passes; maximum/mean host logit delta was 0.05884/0.006884. The strict native C
golden, sanitizer run, 100-sequence ESP32-S3 test, native tokenizer, and full
grounded device generation all pass. `tokenizer.chtk` is the exact 24,194-byte
native tokenizer artifact. See `docs/NATIVE_RESULTS.md` for measured limits.
