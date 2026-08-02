# Circuit Heroes LM Circuit Quest pilot v0.2

This pilot is the smallest honest experiment for running a locally generative,
electronics-focused model on an ESP32-S3. It uses a 52-record hardware
information layer (HIL), retrieves one exact record, asks the PLE TinyLM for a
one-sentence answer or mystery-game clue, verifies the output, and falls back
to a deterministic sentence if verification fails.

## Scope

- 52 real component and module concepts
- beginner explanation, symbol, behavior, and non-revealing game-clue tasks
- fully offline inference after flashing
- 4,097,312 parameters, 4,096-token vocabulary, 256-token context
- 6 decoder layers, width 96, 4 attention heads, PLE width 128
- group-128 ragged INT4 model artifact: 2,124,620 bytes

The HIL has the status `engineering-review-required`. Its records are project
grounding data, not a substitute for component datasheets or an independent
expert safety review.

## Reproduce the corpus

From the repository root, with the locked virtual environment installed:

```sh
.venv/bin/python tools/build_pilot.py
.venv/bin/python tools/tokenize_dataset.py \
  --dataset generated/pilot \
  --tokenizer model-tokenizer.json \
  --output generated/pilot-tokens
```

The corpus contains 5,499 training, 674 validation, and 691 test examples. The
generated C header contains 21,269 prompt tokens; the longest prompt is 131
tokens.

## Reproduce training

```sh
.venv/bin/python training/train.py \
  --arm ple --fixed-ffn 66 --d-model 96 --n-layers 6 --n-heads 4 \
  --ple-dim 128 --seq-len 256 --vocab 4096 --steps 1800 \
  --batch-size 16 --lr 0.001 --warmup 100 --eval-every 100 \
  --eval-iters 20 --early-stop-evals 5 --seed 84 --tag quest-v0_2 \
  --data-dir generated/pilot-tokens
```

The recorded run used about 7.4 million tokens and reached validation loss
0.0750 (perplexity 1.08). These numbers mainly show that the small canonical task
contract was learned; they do not measure broad language understanding.

## Evaluate and export

```sh
.venv/bin/python tools/evaluate_pilot.py \
  --run runs/ple-quest-v0_2-s84-best.pt
.venv/bin/python training/export.py ple-quest-v0_2-s84-best
shasum -a 256 artifacts/model/model.bin
```

The canonical greedy evaluation produces 208 answers and currently reports
208/208 passing identity, factual-overlap, length, uncertainty, and
non-revealing game-clue checks. The exported artifact SHA-256 is:

```text
673fc7d7fbd8110e82150a8f4f519b06dddf2d9c97d2d6d9eb33ae880eefcc10
```

## What this result does not mean

- It does not show generalization to components outside the 52-record HIL.
- It does not pass the production release gates in `MODEL_CARD.md`.
- It does not justify claims of autonomous hardware thinking or “world first.”
- It does not replace datasheets, calculations, or expert review.
- It does not synthesize arbitrary speech; the current product voice is an
  offline clip pack.

The correct product label is **Circuit Heroes LM Circuit Quest pilot v0.2:
bounded, catalogue-grounded local generation on ESP32-S3**.
