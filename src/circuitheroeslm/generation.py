"""Deterministic native generation helpers for circuitheroesLM."""

from __future__ import annotations

import torch

from .model import EngineeringStateRouterLM
from .tokenizer import EngineeringTokenizer
from .tokenizer import SPECIAL_TOKENS


COPY_FIELDS = {
    SPECIAL_TOKENS.index("<copy_name>"): "name",
    SPECIAL_TOKENS.index("<copy_family>"): "family",
    SPECIAL_TOKENS.index("<copy_purpose>"): "purpose",
    SPECIAL_TOKENS.index("<copy_symbol>"): "symbol",
    SPECIAL_TOKENS.index("<copy_behavior>"): "behavior",
    SPECIAL_TOKENS.index("<copy_constraint>"): "constraint",
}


def render_fact_tape(token_ids: list[int], tokenizer: EngineeringTokenizer,
                     fields: dict[str, str] | None) -> str:
    output: list[str] = []
    buffered: list[int] = []

    def flush() -> None:
        if buffered:
            output.append(tokenizer.decode(buffered))
            buffered.clear()

    for token_id in token_ids:
        field = COPY_FIELDS.get(token_id)
        if field is not None:
            flush()
            if fields is None or field not in fields:
                raise ValueError(f"FactTape field unavailable: {field}")
            output.append(fields[field])
        elif token_id >= tokenizer.byte_offset:
            buffered.append(token_id)
    flush()
    return "".join(output).strip()


@torch.no_grad()
def greedy_generate(model: EngineeringStateRouterLM, tokenizer: EngineeringTokenizer,
                    prompt: str, max_new_tokens: int = 64,
                    fact_fields: dict[str, str] | None = None) -> tuple[str, list[int]]:
    model.eval()
    device = next(model.parameters()).device
    prompt_ids = [1] + tokenizer.encode(prompt)
    state = None
    logits = None
    for token_id in prompt_ids[-model.config.context:]:
        logits, state = model.step(torch.tensor([token_id], device=device), state)
    generated: list[int] = []
    blocked = {0, 1}
    for _ in range(max_new_tokens):
        scores = logits[0].clone()
        for token_id in blocked:
            scores[token_id] = -torch.inf
        token_id = int(torch.argmax(scores).item())
        if token_id == 2:
            break
        generated.append(token_id)
        logits, state = model.step(torch.tensor([token_id], device=device), state)
    return render_fact_tape(generated, tokenizer, fact_fields), generated
