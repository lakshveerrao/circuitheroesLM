# Reproduce CircuitLM Quest v0.2

## Environment

Install the locked Python environment with `uv sync`. Training supports CPU,
Apple Metal, and CUDA. Runtime inference remains fully offline.

## Dataset and tokens

```sh
.venv/bin/python tools/build_pilot.py
.venv/bin/python tools/tokenize_dataset.py --dataset generated/pilot \
  --tokenizer model-tokenizer.json --output generated/pilot-tokens
```

## Train

```sh
.venv/bin/python training/train.py --arm ple --fixed-ffn 66 --d-model 96 \
  --n-layers 6 --n-heads 4 --ple-dim 128 --seq-len 256 --vocab 4096 \
  --steps 1800 --batch-size 16 --lr 0.001 --warmup 100 \
  --eval-every 100 --eval-iters 20 --early-stop-evals 5 \
  --seed 84 --tag quest-v0_2 --data-dir generated/pilot-tokens
```

Recorded result: 7,372,800 tokens, 349.5 seconds, validation loss 0.07502,
perplexity 1.07791.

## Evaluate and export

```sh
.venv/bin/python tools/evaluate_pilot.py \
  --run runs/ple-quest-v0_2-s84-best.pt
.venv/bin/python training/export.py ple-quest-v0_2-s84-best
shasum -a 256 artifacts/model/model.bin
```

Expected: 208/208 verifier passes and INT4 SHA-256
`673fc7d7fbd8110e82150a8f4f519b06dddf2d9c97d2d6d9eb33ae880eefcc10`.

## Runtime method

The app retrieves one exact HIL record, builds a task-specific prompt, runs
the decoder-only PLE TinyLM, then rejects output that lacks grounded fact
overlap, invents identity, or reveals a game answer. A deterministic grounded
fallback appears immediately while generation runs. PLE tables and quantized
weights live in flash; working state uses SRAM/PSRAM.

## ESP32-S3 result

On Waveshare ESP32-S3 N16R8, a 104-token game prompt plus 28 generated tokens
took 14,286 ms. The generated clue passed the on-device verifier. Firmware,
model, 8,000-record catalogue, and voice regions passed flash verification.

This is a bounded 52-component pilot, not open-domain electronics reasoning.
