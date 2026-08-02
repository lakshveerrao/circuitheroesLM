"""Train the native engineering byte-BPE tokenizer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from circuitheroeslm.tokenizer import EngineeringTokenizer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="generated/native-pilot-v0.1")
    parser.add_argument("--vocab", type=int, default=1536)
    parser.add_argument("--output", default="generated/native-tokenizer.json")
    parser.add_argument("--include-evaluation-splits", action="store_true")
    args = parser.parse_args()
    texts = []
    paths = sorted((ROOT / args.data).glob("*.jsonl")) if args.include_evaluation_splits else [ROOT / args.data / "train.jsonl"]
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            texts.extend((row["prompt"], row["answer"]))
    tokenizer = EngineeringTokenizer.train(texts, args.vocab)
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    tokenizer.save(output)
    encoded = sum(len(tokenizer.encode(text)) for text in texts)
    raw = sum(len(text.encode("utf-8")) for text in texts)
    print(json.dumps({"project": "circuitheroesLM", "vocab": tokenizer.vocab_size,
                      "texts": len(texts), "utf8_bytes": raw, "tokens": encoded,
                      "bytes_per_token": raw / encoded}, indent=2))


if __name__ == "__main__":
    main()
