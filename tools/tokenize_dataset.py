#!/usr/bin/env python3
"""Tokenize CircuitLM JSONL splits into compact uint16 next-token files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from tokenizers import Tokenizer


def format_example(item: dict) -> tuple[str, str]:
    if item.get("schema") == "circuitlm-pilot-instruction-v1":
        return item["prompt"], " " + item["answer"]
    # The labels are deliberately visible tokens. At inference time the same
    # structure acts as a small hardware-reasoning plan without exposing a long
    # chain of thought to the learner.
    facts = item["verified_facts"]
    prompt = (
        f"Electronics task: {item['task']}\n"
        f"Question: {item['question']}\n"
        f"Verified exact name: {facts['exact_name']}\n"
        f"Verified family: {facts['family']}\n"
        f"Verified description: {facts['description']}\n"
        f"Verified package: {facts['footprint'] or 'not provided'}\n"
        "Answer:"
    )
    return prompt, " " + item["answer"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--tokenizer", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    tokenizer = Tokenizer.from_file(str(args.tokenizer))
    eot = tokenizer.token_to_id("<|endoftext|>")
    if eot is None:
        raise SystemExit("tokenizer has no <|endoftext|> token")
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for split in ("train", "validation", "test"):
        input_path = args.dataset / f"{split}.jsonl"
        ids: list[int] = []
        answer_mask: list[int] = []
        records = 0
        with input_path.open(encoding="utf-8") as handle:
            for line in handle:
                item = json.loads(line)
                prompt, answer = format_example(item)
                prompt_ids = tokenizer.encode(prompt).ids
                answer_ids = tokenizer.encode(answer).ids
                ids.extend(prompt_ids)
                answer_mask.extend([0] * len(prompt_ids))
                ids.extend(answer_ids)
                answer_mask.extend([1] * len(answer_ids))
                ids.append(eot)
                answer_mask.append(1)
                records += 1
        if max(ids, default=0) >= 65536:
            raise SystemExit("token id does not fit uint16")
        output_path = args.output / f"{split}.bin"
        np.asarray(ids, dtype=np.uint16).tofile(output_path)
        mask_path = args.output / f"{split}.answer-mask.bin"
        np.asarray(answer_mask, dtype=np.uint8).tofile(mask_path)
        manifest[split] = {
            "records": records,
            "tokens": len(ids),
            "answer_tokens": sum(answer_mask),
            "file": output_path.name,
            "answer_mask": mask_path.name,
        }
        print(f"{split}: {records} records, {len(ids)} tokens")
    (args.output / "token-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
