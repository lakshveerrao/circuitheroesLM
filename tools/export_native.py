"""Export a native checkpoint to the CHLM v1 row-INT8 reference format."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from circuitheroeslm.format import quantized_state_dict, write_chlm
from circuitheroeslm.model import ESRConfig, EngineeringStateRouterLM


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", default="artifacts/circuitheroeslm-native-v0.3.chlm")
    args = parser.parse_args()
    document = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    if document.get("schema") != "circuitheroeslm-native-checkpoint-v1":
        raise SystemExit("not a native checkpoint")
    config = ESRConfig(**document["config"])
    float_model = EngineeringStateRouterLM(config).eval()
    float_model.load_state_dict(document["state_dict"])
    _, restored = quantized_state_dict(document["state_dict"])
    quantized_model = EngineeringStateRouterLM(config).eval()
    quantized_model.load_state_dict(restored)
    torch.manual_seed(91)
    tokens = torch.randint(0, config.vocab_size, (2, min(32, config.context)))
    with torch.no_grad():
        float_logits, _ = float_model(tokens)
        int8_logits, _ = quantized_model(tokens)
    maximum = (float_logits - int8_logits).abs().max().item()
    mean = (float_logits - int8_logits).abs().mean().item()
    output = ROOT / args.output
    manifest = write_chlm(output, config, document["state_dict"])
    manifest["float_vs_row_int8_max_logit_delta"] = maximum
    manifest["float_vs_row_int8_mean_logit_delta"] = mean
    manifest["sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"output": str(output), "sha256": manifest["sha256"], "bytes": manifest["bytes"],
                      "max_logit_delta": maximum, "mean_logit_delta": mean}, indent=2))


if __name__ == "__main__":
    main()

