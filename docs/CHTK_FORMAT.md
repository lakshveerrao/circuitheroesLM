# CHTK v1 native tokenizer format

CHTK is the independently implemented binary form of the exact tokenizer used
during training. All values are little-endian.

The 40-byte header contains magic `CHTK`, version, endian marker, total file
bytes, vocabulary and merge counts, merge/offset/piece locations, payload CRC32
and a zero reserved word. The payload contains ordered `<left,right,new>`
`uint16` merge triples, a `uint32[vocab+1]` piece-offset table, and a contiguous
UTF-8 byte-piece blob.

The loader rejects inconsistent vocabulary dimensions, non-canonical merge
order, invalid offsets, non-monotonic piece bounds, unknown versions and CRC
failure. The v0.3 artifact has 1,536 tokens, 1,267 merges, is 24,194 bytes, and
has SHA-256 `3f9441df4108d8bca53ffe30b84c222003a14670ae910c44419cca19d2cb978c`.
