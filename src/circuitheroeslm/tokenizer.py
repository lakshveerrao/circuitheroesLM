"""Deterministic engineering byte-pair tokenizer implemented for circuitheroesLM."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path


SPECIAL_TOKENS = ("<pad>", "<bos>", "<eos>", "<fact>", "<ask>", "<answer>", "<unknown>")


@dataclass(frozen=True)
class Merge:
    left: int
    right: int
    token: int


class EngineeringTokenizer:
    """UTF-8 byte tokenizer with a deterministic, corpus-trained merge table."""

    def __init__(self, merges: list[Merge] | None = None):
        self.byte_offset = len(SPECIAL_TOKENS)
        self.merges = list(merges or [])
        self.merge_lookup = {(item.left, item.right): item.token for item in self.merges}
        self.pieces: dict[int, bytes] = {
            self.byte_offset + value: bytes((value,)) for value in range(256)
        }
        for merge in self.merges:
            self.pieces[merge.token] = self.pieces[merge.left] + self.pieces[merge.right]

    @property
    def vocab_size(self) -> int:
        return self.byte_offset + 256 + len(self.merges)

    def _base(self, text: str) -> list[int]:
        return [self.byte_offset + byte for byte in text.encode("utf-8")]

    def encode_text(self, text: str) -> list[int]:
        tokens = self._base(text)
        for merge in self.merges:
            merged: list[int] = []
            index = 0
            while index < len(tokens):
                if index + 1 < len(tokens) and tokens[index] == merge.left and tokens[index + 1] == merge.right:
                    merged.append(merge.token)
                    index += 2
                else:
                    merged.append(tokens[index])
                    index += 1
            tokens = merged
        return tokens

    def encode(self, text: str, *, bos: bool = False, eos: bool = False) -> list[int]:
        output = ([SPECIAL_TOKENS.index("<bos>")] if bos else []) + self.encode_text(text)
        if eos:
            output.append(SPECIAL_TOKENS.index("<eos>"))
        return output

    def decode(self, token_ids: list[int]) -> str:
        raw = bytearray()
        for token_id in token_ids:
            if token_id < self.byte_offset:
                continue
            piece = self.pieces.get(token_id)
            if piece is None:
                raise ValueError(f"unknown token id {token_id}")
            raw.extend(piece)
        return raw.decode("utf-8", errors="replace")

    @classmethod
    def train(cls, texts: list[str], target_vocab: int) -> "EngineeringTokenizer":
        minimum = len(SPECIAL_TOKENS) + 256
        if target_vocab < minimum:
            raise ValueError(f"target vocabulary must be at least {minimum}")
        tokenizer = cls()
        sequences = [tokenizer._base(text) for text in texts if text]
        next_id = minimum
        while next_id < target_vocab:
            counts: Counter[tuple[int, int]] = Counter()
            for sequence in sequences:
                counts.update(zip(sequence, sequence[1:]))
            if not counts:
                break
            best_count = max(counts.values())
            if best_count < 2:
                break
            pair = min(pair for pair, count in counts.items() if count == best_count)
            merge = Merge(pair[0], pair[1], next_id)
            tokenizer.merges.append(merge)
            tokenizer.pieces[next_id] = tokenizer.pieces[pair[0]] + tokenizer.pieces[pair[1]]
            for sequence_index, sequence in enumerate(sequences):
                replaced: list[int] = []
                index = 0
                while index < len(sequence):
                    if index + 1 < len(sequence) and sequence[index] == pair[0] and sequence[index + 1] == pair[1]:
                        replaced.append(next_id)
                        index += 2
                    else:
                        replaced.append(sequence[index])
                        index += 1
                sequences[sequence_index] = replaced
            next_id += 1
        tokenizer.merge_lookup = {(item.left, item.right): item.token for item in tokenizer.merges}
        return tokenizer

    def save(self, path: str | Path) -> None:
        document = {
            "schema": "circuitheroeslm-engineering-tokenizer-v1",
            "special_tokens": list(SPECIAL_TOKENS),
            "byte_offset": self.byte_offset,
            "vocab_size": self.vocab_size,
            "merges": [[item.left, item.right, item.token] for item in self.merges],
        }
        Path(path).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "EngineeringTokenizer":
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        if document.get("schema") != "circuitheroeslm-engineering-tokenizer-v1":
            raise ValueError("unsupported tokenizer schema")
        if tuple(document.get("special_tokens", ())) != SPECIAL_TOKENS:
            raise ValueError("special-token contract mismatch")
        tokenizer = cls([Merge(*values) for values in document["merges"]])
        if tokenizer.vocab_size != document["vocab_size"]:
            raise ValueError("tokenizer vocabulary size mismatch")
        return tokenizer

