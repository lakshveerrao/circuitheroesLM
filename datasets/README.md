# Training datasets

## `pilot-v0.2`

The exact Circuit Quest corpus: 5,499 training, 674 validation, and 691 test
examples across 52 real component concepts and four tasks—explanation, symbol,
behavior, and non-revealing game clue. It includes the source hardware
information layer, generation manifest, and all 208 canonical evaluation
results. Rebuild it with `tools/build_pilot.py`.

## `kicad-grounded-v0.1`

The complete broader research JSONL corpus generated from 21,349 KiCad symbol
records. It is included to reproduce the rejected memorization and grounded
experiments. Family-level splitting keeps related parts together. The source
catalogue is `data/electronics_catalogue.tsv`; provenance is in
`datasets/sources.toml` and `docs/DATASETS.md`.

The pilot HIL is project-authored grounding data marked
`engineering-review-required`. KiCad-derived data follows CC BY-SA 4.0 plus
the KiCad library exception; see `licenses/KiCad-LICENSE.md`.

Token binaries are deliberately reproducible caches, not additional source
data. Generate them with `tools/tokenize_dataset.py` and the checked-in
`model-tokenizer.json`.
