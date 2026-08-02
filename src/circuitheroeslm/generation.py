"""Deterministic native generation helpers for circuitheroesLM."""

from __future__ import annotations

import torch

from .model import EngineeringStateRouterLM
from .tokenizer import EngineeringTokenizer


@torch.no_grad()
def greedy_generate(model: EngineeringStateRouterLM, tokenizer: EngineeringTokenizer,
                    prompt: str, max_new_tokens: int = 64) -> tuple[str, list[int]]:
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
    return tokenizer.decode(generated).strip(), generated

