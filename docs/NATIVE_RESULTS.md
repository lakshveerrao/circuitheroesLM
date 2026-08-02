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
- SHA-256: `da00ffaa8460d608fb614750a92909c75a2a8d1db5ca4284c7b8d9374f1a3cb8`;
- maximum float/INT8 host logit delta: 0.05884;
- mean float/INT8 host logit delta: 0.006884;
- quantized held-out-family evaluation: 864/864 passed.

This opens the native C-runtime gate. It does not yet prove the serialized
artifact executes correctly on ESP32 hardware.

## Native C host verifier

- strict C11 build with warnings-as-errors: pass;
- C vs quantized-PyTorch maximum logit delta: `2.38419e-6`;
- mean logit delta: `4.66059e-7`;
- AddressSanitizer and UndefinedBehaviorSanitizer: pass;
- model/payload/tensor bounds and CRC checks: enabled;
- non-finite kernel values: fail closed.

This opened the ESP32 runtime port gate.

## ESP32-S3 hardware pass

Board: ESP32-S3 revision 0.2, 240 MHz, 16 MB flash, 8 MB octal PSRAM. The model
was memory-mapped from a dedicated flash partition; the tokenizer was embedded
in the probe application. The portable scalar row-INT8 runtime used `-O3`.

- 100 consecutive sequences and 700 total model steps: pass;
- device/reference maximum logit delta: `2.38419e-6`;
- mean delta: `5.05407e-7`;
- compute-only step time: 39.42 ms (25.37 steps/s);
- internal heap before/after: 368,083 / 368,083 bytes;
- PSRAM before/after: 8,380,044 / 8,380,044 bytes;
- native CHTK encode + prompt + six-token grounded answer: 4.605 s;
- final marker: `CIRCUITHEROESLM_NATIVE_DEVICE_PASS`.

The answer generated on the board was: "Transformer is a Magnetically coupled
component that moves alternating-current energy between circuits and changes
voltage."

This proves the declared v0.3 artifact, tokenizer and grounded generation path
execute locally. It does not establish open-domain reasoning or unlimited
component coverage.

## v0.4 — ESR with flash-streamed layer embeddings

- random initialization, 500 steps on Apple MPS, 282.68 seconds;
- 1,163,648 parameters, including 589,824 per-layer embeddings;
- best validation loss 0.263524 (v0.3: 0.2801);
- float and row-INT8 held-out-family evaluation: 864/864 each;
- CHLM artifact: 1,229,312 bytes;
- strict C maximum delta: `4.29153e-6`;
- ESP32-S3 maximum delta: `4.76837e-6`;
- ESP32-S3 100 sequences / 700 steps: pass;
- ESP32-S3 compute: 39.45 ms/token;
- internal heap and PSRAM unchanged before/after;
- native grounded answer: pass in 4.608 s.

v0.4 is the best measured candidate because it improves validation loss without
measurably slowing the device step. Its artifact is roughly twice v0.3's size;
v0.3 remains useful when minimum flash usage matters.
