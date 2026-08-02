#!/usr/bin/env python3
"""Build a deterministic, downloadable CircuitLM model bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAGIC = 0x504C4531


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_model(path: Path) -> dict:
    header = path.read_bytes()[:40]
    if len(header) != 40:
        raise SystemExit("model is too small")
    magic, vocab, dim, layers, heads, ffn, ple, context, group, theta = struct.unpack(
        "<I8if", header
    )
    if magic != MAGIC:
        raise SystemExit("not a supported PLE model")
    parameters = (
        vocab * dim
        + layers * ple * dim
        + ple
        + vocab * layers * ple
        + layers
        * (
            dim
            + 3 * dim * dim
            + dim * dim
            + dim
            + ffn * dim
            + ffn * dim
            + dim * ffn
            + ple * dim
            + dim * ple
            + dim
        )
        + dim
    )
    return {
        "format": "ple-int4-v1",
        "parameters": parameters,
        "vocabulary": vocab,
        "hidden_size": dim,
        "layers": layers,
        "attention_heads": heads,
        "ffn_size": ffn,
        "ple_size": ple,
        "context_tokens": context,
        "quant_group": group,
        "rope_theta": theta,
    }


def add_file(stage: Path, source: Path, name: str, files: list[dict]) -> None:
    target = stage / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    files.append({"path": name, "bytes": target.stat().st_size, "sha256": sha256(target)})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--tokenizer", required=True, type=Path)
    parser.add_argument("--catalogue", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--version", default="0.1.0-dev")
    args = parser.parse_args()
    for path in (args.model, args.tokenizer, args.catalogue):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")

    with tempfile.TemporaryDirectory(prefix="circuitlm-release-") as temp:
        stage = Path(temp) / f"Circuit-Heroes-LM-{args.version}"
        stage.mkdir()
        files: list[dict] = []
        add_file(stage, args.model, "model/circuitlm.bin", files)
        add_file(stage, args.tokenizer, "model/tokenizer.json", files)
        add_file(stage, args.catalogue, "model/electronics-pack.bin", files)
        add_file(stage, ROOT / "MODEL_CARD.md", "MODEL_CARD.md", files)
        add_file(stage, ROOT / "README.md", "README.md", files)
        add_file(stage, ROOT / "config" / "hardware_profiles.json", "config/hardware_profiles.json", files)
        add_file(stage, ROOT / "config" / "circuitlm_config_base.h", "include/circuitlm_config_base.h", files)
        add_file(stage, ROOT / "include" / "circuitlm.h", "include/circuitlm.h", files)
        add_file(stage, ROOT / "include" / "circuitlm_board.h", "include/circuitlm_board.h", files)
        add_file(stage, ROOT / "src" / "circuitlm.c", "src/circuitlm.c", files)
        add_file(stage, ROOT / "tools" / "configure.py", "tools/configure.py", files)
        add_file(stage, ROOT / "examples" / "minimal.cpp", "examples/minimal.cpp", files)
        runtime = ROOT / "include" / "circuitlm_ple_runtime.h"
        add_file(stage, runtime, "include/circuitlm_ple_runtime.h", files)
        vocab = ROOT / "include" / "circuitlm_vocab.h"
        add_file(stage, vocab, "include/circuitlm_vocab.h", files)
        notice = ROOT / "licenses" / "slvdev-esp32-ai-MIT.txt"
        add_file(stage, notice, "licenses/slvdev-esp32-ai-MIT.txt", files)
        add_file(stage, ROOT / "licenses" / "KiCad-LICENSE.md", "licenses/KiCad-LICENSE.md", files)
        add_file(stage, ROOT / "LICENSE", "LICENSE", files)
        add_file(stage, ROOT / "NOTICE", "NOTICE", files)
        add_file(stage, ROOT / "AUTHORS.md", "AUTHORS.md", files)
        add_file(stage, ROOT / "docs" / "ARCHITECTURE.md", "docs/ARCHITECTURE.md", files)
        add_file(stage, ROOT / "docs" / "HARDWARE.md", "docs/HARDWARE.md", files)

        manifest = {
            "schema": "circuitlm-bundle-v1",
            "name": "Circuit Heroes LM",
            "creator": "Laksh",
            "version": args.version,
            "offline": True,
            "model": inspect_model(args.model),
            "files": sorted(files, key=lambda item: item["path"]),
        }
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    info = zipfile.ZipInfo(str(path.relative_to(stage.parent)))
                    info.date_time = (2026, 1, 1, 0, 0, 0)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, path.read_bytes())
    print(f"wrote {args.output} ({args.output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
