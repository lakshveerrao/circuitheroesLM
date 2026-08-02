# Native results

## v0.1 — rejected

Single-template corpus and working-state-only ESR. Training loss improved, but
both validation and held-out generation samples scored 0/12. The model emitted
memorized components instead of grounding on the prompt.

## v0.2 — rejected

Added explicit segment tokens, protected fact latch and 12 paraphrase pairs per
task. Validation loss improved to 0.430, but a 24-example held-out sample still
scored 0/24 because exact unseen fields could not be reproduced reliably.

## v0.3 — bounded development pass

Added Engineering FactTape operations. The ESR model generates response plans
containing typed field operations; the runtime resolves exact values from the
retrieved engineering record.

- 573,824 parameters, random initialization;
- 500 steps, 137.1 seconds on CPU;
- best validation loss 0.2801;
- 864/864 held-out-family checks passed;
- 144/144 passes each for explanation, identification, symbol, behavior,
  constraint and game tasks.

This opens the quantization gate. It does not open the ESP32 release gate.

## Native row-INT8 export

- CHLM v1 artifact size: 614,848 bytes;
- SHA-256: `6ec1c54939cc8cfb4b9138254bc3508a9fc1a1f9bcc2d74d0a9db1bc97d7be07`;
- maximum float/INT8 host logit delta: 0.05884;
- mean float/INT8 host logit delta: 0.006884;
- quantized held-out-family evaluation: 864/864 passed.

This opens the native C-runtime gate. It does not yet prove the serialized
artifact executes correctly on ESP32 hardware.
