"""Evaluate native generation on validation and held-out engineering families."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from circuitheroeslm.generation import greedy_generate
from circuitheroeslm.format import quantized_state_dict
from circuitheroeslm.model import ESRConfig, EngineeringStateRouterLM
from circuitheroeslm.tokenizer import EngineeringTokenizer

STOP = {"the", "a", "an", "and", "or", "to", "of", "in", "it", "its", "is", "as", "with", "this", "that"}


def words(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 2 and word not in STOP}


def facts(prompt: str) -> dict[str, str]:
    output = {}
    for line in prompt.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            output[key] = value
    return output


def verify(row: dict, generated: str) -> tuple[bool, str]:
    card = facts(row["prompt"])
    if not generated or len(generated) > 240:
        return False, "empty-or-long"
    if row["task"] == "identify":
        return (card["name"].lower() in generated.lower(), "identity")
    if row["task"] == "game" and card["name"].lower() in generated.lower():
        return False, "revealed-answer"
    field = row["grounded_fields"][0]
    field_key = "constraint" if field == "safety" else field
    expected = words(card[field_key])
    overlap = len(words(generated) & expected)
    return (overlap >= min(2, len(expected)), f"grounded-overlap-{overlap}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--split", default="test-heldout-family")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--component-id", default="")
    parser.add_argument("--row-int8", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    tokenizer = EngineeringTokenizer.load(ROOT / "generated/native-tokenizer.json")
    document = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    if document.get("schema") != "circuitheroeslm-native-checkpoint-v1":
        raise SystemExit("not a native circuitheroesLM checkpoint")
    model = EngineeringStateRouterLM(ESRConfig(**document["config"]))
    state_dict = document["state_dict"]
    if args.row_int8:
        _, state_dict = quantized_state_dict(state_dict)
    model.load_state_dict(state_dict)
    rows = [json.loads(line) for line in (ROOT / f"generated/native-pilot-v0.1/{args.split}.jsonl").read_text().splitlines()]
    if args.component_id:
        rows = [row for row in rows if row["component_id"] == args.component_id]
    if args.limit:
        rows = rows[:args.limit]
    results = []
    for index, row in enumerate(rows):
        generated, token_ids = greedy_generate(model, tokenizer, row["prompt"], fact_fields=facts(row["prompt"]))
        passed, reason = verify(row, generated)
        results.append({"component_id": row["component_id"], "family": row["family"], "task": row["task"],
                        "expected": row.get("rendered_answer", row["answer"]), "generated": generated, "tokens": len(token_ids),
                        "passed": passed, "reason": reason})
        if not args.quiet:
            print(f"{index+1}/{len(rows)} {row['task']} {'PASS' if passed else 'FAIL'}: {generated}")
    task_counts = Counter(row["task"] for row in rows)
    task_passes = Counter(item["task"] for item in results if item["passed"])
    summary = {"schema": "circuitheroeslm-native-evaluation-v1", "project": "circuitheroesLM",
               "checkpoint": args.checkpoint, "quantization": "row-int8" if args.row_int8 else "float32",
               "split": args.split, "total": len(results),
               "passed": sum(item["passed"] for item in results),
               "pass_rate": sum(item["passed"] for item in results) / len(results),
               "by_task": {task: {"passed": task_passes[task], "total": count} for task, count in task_counts.items()},
               "results": results}
    quantization_tag = "-row-int8" if args.row_int8 else ""
    selection_tag = f"-{args.component_id}" if args.component_id else (f"-first-{args.limit}" if args.limit else "")
    output = ROOT / f"generated/{Path(args.checkpoint).stem}-{args.split}{selection_tag}{quantization_tag}-evaluation.json"
    output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({key: value for key, value in summary.items() if key != "results"}, indent=2))


if __name__ == "__main__":
    main()
