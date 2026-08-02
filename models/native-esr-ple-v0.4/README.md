# circuitheroesLM ESR + layer embeddings v0.4

Best measured candidate trained from random initialization with the independent
circuitheroesLM implementation. It adds a flash-streamed, layer-specific token
embedding table to ESR. The published idea is attributed to Gemma 3n PLE; this
is not a Gemma model and contains no Gemma weights or source code.

| Field | Value |
| --- | ---: |
| Parameters | 1,163,648 |
| Layer-embedding parameters | 589,824 |
| Vocabulary | 1,536 |
| ESR layers | 4 |
| Context | 128 |
| Best validation loss | 0.263524 |
| Float held-out-family verifier | 864/864 |
| Row-INT8 held-out-family verifier | 864/864 |
| CHLM bytes | 1,229,312 |
| ESP32-S3 compute | 39.45 ms/token |
| 100-sequence device stability | pass |

The board generated the same grounded Transformer answer as the host verifier.
The result is bounded to the declared task/data contract and is not evidence of
general-purpose or perfect engineering reasoning.
