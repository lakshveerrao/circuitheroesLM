"""Train circuitheroesLM ESR weights from random initialization."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
import time

import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from circuitheroeslm.model import ESRConfig, EngineeringStateRouterLM
from circuitheroeslm.tokenizer import EngineeringTokenizer


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def encode_row(row: dict, tokenizer: EngineeringTokenizer, context: int) -> tuple[list[int], list[int]]:
    prefix = [1] + tokenizer.encode(row["prompt"])
    full = prefix + tokenizer.encode(row["answer"]) + [2]
    full = full[: context + 1]
    x, y = full[:-1], full[1:]
    answer_start = min(len(prefix) - 1, len(y))
    labels = [-100] * answer_start + y[answer_start:]
    return x, labels


def batch(rows: list[dict], tokenizer: EngineeringTokenizer, context: int, count: int, rng: random.Random, device: str):
    chosen = [rng.choice(rows) for _ in range(count)]
    encoded = [encode_row(row, tokenizer, context) for row in chosen]
    length = max(len(item[0]) for item in encoded)
    x = torch.zeros((count, length), dtype=torch.long)
    y = torch.full((count, length), -100, dtype=torch.long)
    for index, (tokens, labels) in enumerate(encoded):
        x[index, :len(tokens)] = torch.tensor(tokens)
        y[index, :len(labels)] = torch.tensor(labels)
    return x.to(device), y.to(device)


@torch.no_grad()
def validation_loss(model, rows, tokenizer, config, device):
    model.eval()
    rng = random.Random(17)
    losses = []
    for _ in range(min(8, len(rows))):
        x, y = batch(rows, tokenizer, config.context, min(4, len(rows)), rng, device)
        logits, _ = model(x)
        losses.append(F.cross_entropy(logits.reshape(-1, config.vocab_size), y.reshape(-1), ignore_index=-100).item())
    model.train()
    return sum(losses) / len(losses)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--lr", type=float, default=8e-4)
    parser.add_argument("--seed", type=int, default=20260802)
    parser.add_argument("--tag", default="native-pilot-v0.1")
    parser.add_argument("--per-layer-embeddings", action="store_true")
    args = parser.parse_args()
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer_path = ROOT / "generated" / "native-tokenizer.json"
    tokenizer = EngineeringTokenizer.load(tokenizer_path)
    config = ESRConfig(vocab_size=tokenizer.vocab_size,
                       per_layer_embeddings=args.per_layer_embeddings)
    model = EngineeringStateRouterLM(config).to(device)
    train = load_rows(ROOT / "generated/native-pilot-v0.1/train.jsonl")
    validation = load_rows(ROOT / "generated/native-pilot-v0.1/validation.jsonl")
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, betas=(0.9, 0.98), weight_decay=0.01)
    rng = random.Random(args.seed)
    started = time.perf_counter()
    history = []
    best = float("inf")
    run_dir = ROOT / "runs"
    run_dir.mkdir(exist_ok=True)
    for step in range(1, args.steps + 1):
        x, y = batch(train, tokenizer, config.context, args.batch, rng, device)
        logits, _ = model(x)
        loss = F.cross_entropy(logits.reshape(-1, config.vocab_size), y.reshape(-1), ignore_index=-100)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if step == 1 or step % 25 == 0 or step == args.steps:
            val = validation_loss(model, validation, tokenizer, config, device)
            point = {"step": step, "train_loss": loss.item(), "validation_loss": val}
            history.append(point)
            print(json.dumps(point), flush=True)
            if val < best:
                best = val
                torch.save({"schema": "circuitheroeslm-native-checkpoint-v1", "project": "circuitheroesLM",
                            "config": config.to_dict(), "state_dict": model.state_dict(),
                            "tokenizer_sha256": hashlib.sha256(tokenizer_path.read_bytes()).hexdigest(),
                            "step": step, "validation_loss": val, "seed": args.seed},
                           run_dir / f"{args.tag}-best.pt")
    manifest = {"schema": "circuitheroeslm-native-run-v1", "project": "circuitheroesLM",
                "architecture": "Engineering State Router", "device": device,
                "random_initialization": True, "seed": args.seed, "steps": args.steps,
                "wall_seconds": time.perf_counter() - started, "best_validation_loss": best,
                "parameters": model.parameter_report(), "config": config.to_dict(), "history": history}
    (run_dir / f"{args.tag}.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
