# circuitheroesLM ESR + layer embeddings v0.4

Best measured candidate trained from random initialization with the
circuitheroesLM implementation. It adds a flash-streamed, layer-specific token
embedding table to ESR. The published PLE method is attributed to Google Gemma
3n; circuitheroesLM adapts it to ESR and mapped microcontroller flash.

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
