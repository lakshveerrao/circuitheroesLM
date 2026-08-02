"""Build the native engineering-only circuitheroesLM pilot corpus."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "engineering_hil_v0.1.json"
OUTPUT = ROOT / "generated" / "native-pilot-v0.1"


def fact_card(component: dict) -> str:
    return (
        "<fact>\n"
        f"name={component['name']}\nfamily={component['family']}\n"
        f"purpose={component['purpose']}\nsymbol={component['symbol']}\n"
        f"behavior={component['behavior']}\nconstraint={component['safety']}\n"
    )


def examples(component: dict) -> list[dict]:
    card = fact_card(component)
    tasks = [
        ("explain", "Explain this component simply.", f"{component['name']} {component['purpose']}.", ["purpose"]),
        ("identify", f"Which component {component['purpose']}?", component["name"] + ".", ["name"]),
        ("symbol", "Describe only its circuit symbol.", component["symbol"].capitalize() + ".", ["symbol"]),
        ("behavior", "What happens inside or while it works?", component["behavior"].capitalize() + ".", ["behavior"]),
        ("constraint", "Give one important engineering caution.", component["safety"].capitalize() + ".", ["safety"]),
        ("game", "Create a mystery clue without saying the component name.", "Choose the part that " + component["purpose"] + ".", ["purpose"]),
    ]
    output = []
    for task, question, answer, fields in tasks:
        output.append({
            "schema": "circuitheroeslm-native-example-v1",
            "component_id": component["id"],
            "family": component["family"],
            "task": task,
            "prompt": card + f"<ask>\ntask={task}\nquestion={question}\n<answer>\n",
            "answer": answer,
            "grounded_fields": fields,
        })
    return output


def main() -> None:
    document = json.loads(SOURCE.read_text(encoding="utf-8"))
    if document.get("license") != "CC0-1.0":
        raise SystemExit("native pilot expects the attributed CC0 HIL")
    records = [item for component in document["components"] for item in examples(component)]
    random.Random(20260802).shuffle(records)
    family_names = sorted({record["family"] for record in records})
    heldout = set(family_names[::5])
    train = [record for record in records if record["family"] not in heldout]
    test = [record for record in records if record["family"] in heldout]
    validation = train[::9]
    train = [record for index, record in enumerate(train) if index % 9]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, rows in (("train", train), ("validation", validation), ("test-heldout-family", test)):
        payload = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
        path = OUTPUT / f"{name}.jsonl"
        path.write_text(payload, encoding="utf-8")
        hashes[path.name] = hashlib.sha256(payload.encode()).hexdigest()
    manifest = {
        "schema": "circuitheroeslm-native-corpus-v1",
        "project": "circuitheroesLM",
        "source": str(SOURCE.relative_to(ROOT)),
        "source_license": document["license"],
        "review_status": document["review_status"],
        "components": len(document["components"]),
        "tasks": ["explain", "identify", "symbol", "behavior", "constraint", "game"],
        "heldout_families": sorted(heldout),
        "counts": {"train": len(train), "validation": len(validation), "test-heldout-family": len(test)},
        "sha256": hashes,
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

