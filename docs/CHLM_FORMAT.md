# CHLM v1 native model format

All integers are little-endian. Invalid versions, offsets, dimensions, hashes
or CRCs must be rejected before inference.

## 64-byte header

| Field | Type |
| --- | --- |
| magic | `char[4]`, `CHLM` |
| version | `uint16`, currently 1 |
| endian marker | `uint16`, `0x1234` |
| total file bytes | `uint32` |
| tensor count and flags | two `uint32` |
| vocab, width, layers, lanes, state width, mixer width, context | seven `uint32` |
| norm epsilon | `float32` |
| directory offset, data offset, payload CRC32 | three `uint32` |

## 64-byte tensor directory entry

Each entry contains FNV-1a name hash, dtype, rank, four dimensions, data and
scale offsets/lengths, separate CRC32 values and reserved words. Tensor hashes
are collision-checked during export. Payloads are 16-byte aligned. Unused
dimension slots are padded with `1` and rejected if they contain another value.

## Dtypes

- `1`: raw float32, used for vectors and biases;
- `2`: row-wise symmetric INT8 matrix plus one float32 scale per flattened row.

For a matrix row `w`, export computes `scale=max(abs(w))/127`, stores
`round(w/scale)` clipped to `[-127,127]`, and reconstructs `code*scale`.

The format and exporter were implemented for circuitheroesLM on the native
branch; they do not use the prototype PLE model format.

Flag bit 0 declares the optional `layer_embeddings` tensor with shape
`[layers,vocab,width]`. The row-INT8 scales are indexed by flattened
`layer*vocab+token`, permitting one contiguous flash row to be read per layer.
All other flag bits are rejected.

CHLM contains model tensors only. The matching native tokenizer is the
separate, checksummed CHTK artifact documented in `CHTK_FORMAT.md`.
