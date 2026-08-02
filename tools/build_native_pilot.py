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
    tasks = {
        "explain": {
            "questions": ["Explain this component simply.", "What is this part for?", "Teach this part in one sentence.", "Give a beginner explanation."],
            "answers": ["<copy_name> <copy_purpose>.",
                        "<copy_name> is a <copy_family> that <copy_purpose>.",
                        "This is <copy_name>; it <copy_purpose>."] ,
            "fields": ["purpose"],
        },
        "identify": {
            "questions": [f"Which component {component['purpose']}?", "Name the component in this fact card.",
                          "What is the exact part name?", "Identify this engineering component."],
            "answers": ["<copy_name>.", "The component is <copy_name>.", "Choose <copy_name>."],
            "fields": ["name"],
        },
        "symbol": {
            "questions": ["Describe only its circuit symbol.", "How is its symbol drawn?", "What symbol represents this part?", "Explain the schematic symbol."],
            "answers": ["<copy_symbol>.", "Its symbol is <copy_symbol>.",
                        "On a schematic, look for <copy_symbol>."] ,
            "fields": ["symbol"],
        },
        "behavior": {
            "questions": ["What happens inside or while it works?", "Explain its operating behavior.", "How does this component work?", "What physical or electrical change occurs?"],
            "answers": ["<copy_behavior>.", "It works like this: <copy_behavior>.",
                        "During operation, <copy_behavior>."] ,
            "fields": ["behavior"],
        },
        "constraint": {
            "questions": ["Give one important engineering caution.", "What must a builder check?", "State one safe-use constraint.", "What mistake should be avoided?"],
            "answers": ["<copy_constraint>.", "Important: <copy_constraint>.",
                        "A builder must remember: <copy_constraint>."] ,
            "fields": ["safety"],
        },
        "game": {
            "questions": ["Create a mystery clue without saying the component name.", "Write a choose-the-part game clue.",
                          "Challenge the player using its purpose.", "Make one grounded mystery mission."],
            "answers": ["Choose the part that <copy_purpose>.",
                        "Mystery mission: find the part that <copy_purpose>.",
                        "Which hidden part <copy_purpose>?"],
            "fields": ["purpose"],
        },
    }
    output = []
    for task, contract in tasks.items():
        for question in contract["questions"]:
            for answer in contract["answers"]:
                output.append({
                    "schema": "circuitheroeslm-native-example-v1",
                    "component_id": component["id"],
                    "family": component["family"],
                    "task": task,
                    "prompt": card + f"<ask>\ntask={task}\nquestion={question}\n<answer>\n",
                    "answer": answer,
                    "rendered_answer": (answer.replace("<copy_name>", component["name"])
                                              .replace("<copy_family>", component["family"].lower())
                                              .replace("<copy_purpose>", component["purpose"])
                                              .replace("<copy_symbol>", component["symbol"])
                                              .replace("<copy_behavior>", component["behavior"])
                                              .replace("<copy_constraint>", component["safety"])),
                    "grounded_fields": contract["fields"],
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
