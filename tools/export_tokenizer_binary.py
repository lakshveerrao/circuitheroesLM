"""Export the circuitheroesLM tokenizer to the native CHTK v1 format."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib


MAGIC = b"CHTK"
VERSION = 1
ENDIAN = 0x1234
HEADER_BYTES = 40
SPECIAL_COUNT = 13


def align4(value: int) -> int:
    return (value + 3) & ~3


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    document = json.loads(Path(args.tokenizer).read_text(encoding="utf-8"))
    if document.get("schema") != "circuitheroeslm-engineering-tokenizer-v1":
        raise SystemExit("unsupported tokenizer schema")
    vocab = int(document["vocab_size"])
    merges = [tuple(map(int, merge)) for merge in document["merges"]]
    if vocab != SPECIAL_COUNT + 256 + len(merges) or vocab > 65535:
        raise SystemExit("invalid tokenizer dimensions")
    pieces: list[bytes] = [b""] * vocab
    for value in range(256):
        pieces[SPECIAL_COUNT + value] = bytes((value,))
    expected_token = SPECIAL_COUNT + 256
    for left, right, token in merges:
        if token != expected_token or left >= token or right >= token:
            raise SystemExit("non-canonical merge table")
        pieces[token] = pieces[left] + pieces[right]
        expected_token += 1
    merge_offset = HEADER_BYTES
    offsets_offset = align4(merge_offset + len(merges) * 6)
    pieces_offset = offsets_offset + (vocab + 1) * 4
    offsets = [0]
    blob = bytearray()
    for piece in pieces:
        blob.extend(piece)
        offsets.append(len(blob))
    image = bytearray(pieces_offset + len(blob))
    cursor = merge_offset
    for merge in merges:
        struct.pack_into("<HHH", image, cursor, *merge)
        cursor += 6
    struct.pack_into(f"<{len(offsets)}I", image, offsets_offset, *offsets)
    image[pieces_offset:] = blob
    payload_crc = zlib.crc32(image[merge_offset:])
    struct.pack_into("<4sHH8I", image, 0, MAGIC, VERSION, ENDIAN, len(image), vocab,
                     len(merges), merge_offset, offsets_offset, pieces_offset,
                     payload_crc, 0)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image)
    manifest = {
        "schema": "circuitheroeslm-chtk-v1-manifest",
        "format": "CHTK",
        "version": VERSION,
        "bytes": len(image),
        "vocab_size": vocab,
        "merge_count": len(merges),
        "sha256": hashlib.sha256(image).hexdigest(),
        "source_sha256": hashlib.sha256(Path(args.tokenizer).read_bytes()).hexdigest(),
    }
    output.with_suffix(output.suffix + ".json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
