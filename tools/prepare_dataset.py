#!/usr/bin/env python3
"""Create a deterministic, provenance-preserving electronics instruction set."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path


def clean(text: str, limit: int = 220) -> str:
    return re.sub(r"\s+", " ", text).strip()[:limit]


def stable_group(value: str) -> int:
    return int.from_bytes(hashlib.sha256(value.encode()).digest()[:8], "little") % 100


def record(source: dict, task: str, question: str, answer: str) -> dict:
    return {
        "schema": "circuitlm-instruction-v1",
        "task": task,
        "question": clean(question),
        "answer": clean(answer),
        "component": clean(source["name"]),
        "family": clean(source["category"]),
        "source": clean(source["source"]),
        "verified_input": True,
        "verified_facts": {
            "exact_name": clean(source["name"]),
            "family": clean(source["category"]),
            "description": clean(source["description"]),
            "footprint": clean(source.get("footprint", "")),
        },
    }


def examples(row: dict) -> list[dict]:
    name = clean(row["name"])
    family = clean(row["category"])
    desc = clean(row["description"])
    footprint = clean(row.get("footprint", ""))
    output = [
        record(row, "identity", "What is the exact name of this component?", name),
        record(row, "type", f"What type of electronic part is {name}?", family),
        record(row, "purpose", f"What does {name} do?", desc),
        record(
            row,
            "beginner_explanation",
            f"Explain {name} to a child who is new to electronics.",
            f"{name} is a {family.lower()}. In simple terms: {desc}",
        ),
    ]
    if footprint:
        output.append(
            record(row, "appearance", f"How is {name} packaged or mounted?", footprint)
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalogue", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    with args.catalogue.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows or not {"category", "name", "description", "source"} <= rows[0].keys():
        raise SystemExit("catalogue does not match the expected KiCad TSV schema")

    splits: dict[str, list[dict]] = {"train": [], "validation": [], "test": []}
    for row in rows:
        # Split entire source families together. Test data therefore measures
        # transfer instead of memorizing sibling part numbers.
        bucket = stable_group(row["category"])
        split = "train" if bucket < 80 else "validation" if bucket < 90 else "test"
        splits[split].extend(examples(row))

    rng = random.Random(args.seed)
    args.output.mkdir(parents=True, exist_ok=True)
    summary = {"source_rows": len(rows), "splits": {}, "tasks": {}}
    all_tasks: Counter[str] = Counter()
    for split, items in splits.items():
        rng.shuffle(items)
        path = args.output / f"{split}.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for item in items:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
                all_tasks[item["task"]] += 1
        summary["splits"][split] = len(items)
    summary["tasks"] = dict(sorted(all_tasks.items()))
    summary["catalogue_sha256"] = hashlib.sha256(args.catalogue.read_bytes()).hexdigest()
    (args.output / "dataset-manifest.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
