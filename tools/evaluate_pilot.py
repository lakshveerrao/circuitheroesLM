#!/usr/bin/env python3
"""Run deterministic, release-blocking qualitative checks for the pilot model."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import torch
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "training"))
from model import Config, TinyLM  # noqa: E402
from build_pilot import TASKS, prompt  # noqa: E402


STOPWORDS = {"the", "and", "with", "from", "that", "this", "into", "when", "its", "one", "two", "three", "their", "between", "inside"}


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2 and w not in STOPWORDS}


def greedy(model: TinyLM, tokenizer: Tokenizer, text: str, limit: int) -> str:
    device = next(model.parameters()).device
    input_ids = tokenizer.encode(text).ids
    ids = torch.tensor([input_ids], device=device)
    eot = tokenizer.token_to_id("<|endoftext|>")
    with torch.no_grad():
        for _ in range(limit):
            logits, _ = model(ids[:, -model.cfg.seq_len :])
            token = int(torch.argmax(logits[0, -1]).item())
            if token == eot:
                break
            ids = torch.cat((ids, torch.tensor([[token]], device=device)), dim=1)
    return tokenizer.decode(ids[0, len(input_ids) :].tolist()).strip().splitlines()[0]


def target_text(record: dict, task: str) -> str:
    if task == "game":
        return record["purpose"] + " " + record["behavior"]
    return record["purpose" if task == "explain" else task]


def verify(record: dict, task: str, answer: str) -> tuple[bool, list[str]]:
    failures = []
    answer_words = words(answer)
    target_words = words(target_text(record, task))
    anchors = {a.lower() for a in record["anchors"]}
    name_words = words(record["name"])
    if len(answer) < 18 or len(answer) > 220:
        failures.append("length")
    # The behavior slide already displays the exact component title, so it may
    # use a pronoun. Explain and symbol answers must still identify the part.
    if task in ("explain", "symbol") and not (
        answer_words & anchors or len(answer_words & name_words) >= min(2, len(name_words))
    ):
        failures.append("identity-anchor")
    if task == "game" and record["name"].lower() in answer.lower():
        failures.append("reveals-answer")
    if len(answer_words & target_words) < 2:
        failures.append("fact-overlap")
    if any(term in answer.lower() for term in ("i don't know", "as an ai", "internet", "maybe", "probably")):
        failures.append("uncertain-or-meta")
    return not failures, failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--hil", type=Path, default=ROOT / "pilot" / "hil_v0_1.json")
    parser.add_argument("--tokenizer", type=Path, default=ROOT / "model-tokenizer.json")
    parser.add_argument("--output", type=Path, default=ROOT / "generated" / "pilot-evaluation.json")
    parser.add_argument("--tokens", type=int, default=48)
    parser.add_argument("--max-failures", type=int, default=0)
    args = parser.parse_args()

    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    checkpoint = torch.load(args.run, map_location=device, weights_only=False)
    model = TinyLM(Config(**checkpoint["cfg"])).to(device)
    model.load_state_dict(checkpoint["state"])
    model.eval()
    tokenizer = Tokenizer.from_file(str(args.tokenizer))
    records = json.loads(args.hil.read_text())["components"]
    results = []
    passed = 0
    for record_index, record in enumerate(records):
        for task in TASKS:
            answer = greedy(model, tokenizer, prompt(record, task), args.tokens)
            valid, failures = verify(record, task, answer)
            passed += int(valid)
            results.append({
                "component_index": record_index,
                "component": record["name"],
                "task": task,
                "passed": valid,
                "failures": failures,
                "answer": answer,
            })
    total = len(results)
    report = {
        "schema": "circuitlm-pilot-evaluation-v1",
        "checkpoint": str(args.run),
        "device": device,
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": passed / total,
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("total", "passed", "failed", "pass_rate", "device")}, indent=2))
    for result in results:
        if not result["passed"]:
            print(f"FAIL {result['component']} / {result['task']}: {result['failures']} :: {result['answer']}")
    if total - passed > args.max_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
