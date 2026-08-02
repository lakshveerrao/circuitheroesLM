"""Engineering State Router reference model, implemented for circuitheroesLM."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import torch
from torch import Tensor, nn
import torch.nn.functional as F


@dataclass(frozen=True)
class ESRConfig:
    vocab_size: int = 1536
    width: int = 96
    layers: int = 4
    lanes: int = 4
    state_width: int = 32
    mixer_width: int = 192
    context: int = 128
    norm_epsilon: float = 1e-6

    def validate(self) -> None:
        for name in ("vocab_size", "width", "layers", "lanes", "state_width", "mixer_width", "context"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.lanes != 4:
            raise ValueError("native pilot contract requires four engineering lanes")

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


class RootMeanSquareNorm(nn.Module):
    def __init__(self, width: int, epsilon: float):
        super().__init__()
        self.scale = nn.Parameter(torch.ones(width))
        self.epsilon = epsilon

    def forward(self, values: Tensor) -> Tensor:
        energy = values.square().mean(dim=-1, keepdim=True)
        return values * torch.rsqrt(energy + self.epsilon) * self.scale


class EngineeringStateLayer(nn.Module):
    def __init__(self, config: ESRConfig):
        super().__init__()
        d, k, s = config.width, config.lanes, config.state_width
        self.lanes = k
        self.state_width = s
        self.pre_norm = RootMeanSquareNorm(d, config.norm_epsilon)
        self.proposal = nn.Linear(d, k * s)
        self.write = nn.Linear(d, k * s)
        self.recurrent_scale = nn.Parameter(torch.zeros(k, s))
        self.router = nn.Linear(d, k)
        self.state_output = nn.Linear(k * s, d, bias=False)
        self.post_norm = RootMeanSquareNorm(d, config.norm_epsilon)
        self.gate = nn.Linear(d, config.mixer_width)
        self.value = nn.Linear(d, config.mixer_width)
        self.down = nn.Linear(config.mixer_width, d, bias=False)

    def step(self, token: Tensor, state: Tensor) -> tuple[Tensor, Tensor]:
        normalized = self.pre_norm(token)
        proposal = self.proposal(normalized).view(-1, self.lanes, self.state_width)
        proposal = torch.tanh(proposal + self.recurrent_scale * state)
        write = torch.sigmoid(self.write(normalized).view_as(proposal))
        next_state = state + write * (proposal - state)

        route = torch.softmax(self.router(normalized), dim=-1).unsqueeze(-1)
        routed = (next_state * route).reshape(token.shape[0], -1)
        token = token + self.state_output(routed)

        mixed_input = self.post_norm(token)
        mixed = F.silu(self.gate(mixed_input)) * self.value(mixed_input)
        return token + self.down(mixed), next_state


class EngineeringStateRouterLM(nn.Module):
    def __init__(self, config: ESRConfig):
        super().__init__()
        config.validate()
        self.config = config
        self.embedding = nn.Embedding(config.vocab_size, config.width)
        self.blocks = nn.ModuleList(EngineeringStateLayer(config) for _ in range(config.layers))
        self.final_norm = RootMeanSquareNorm(config.width, config.norm_epsilon)
        self.output_bias = nn.Parameter(torch.zeros(config.vocab_size))
        self.reset_native_parameters()

    def reset_native_parameters(self) -> None:
        """Apply the explicit initialization contract used for every native run."""
        for module in self.modules():
            if isinstance(module, (nn.Linear, nn.Embedding)):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)
                if isinstance(module, nn.Linear) and module.bias is not None:
                    nn.init.zeros_(module.bias)
        for block in self.blocks:
            nn.init.zeros_(block.recurrent_scale)
        nn.init.zeros_(self.output_bias)

    def empty_state(self, batch: int, *, device=None, dtype=None) -> tuple[Tensor, ...]:
        shape = (batch, self.config.lanes, self.config.state_width)
        return tuple(torch.zeros(shape, device=device, dtype=dtype) for _ in self.blocks)

    def step(self, token_ids: Tensor, state: tuple[Tensor, ...] | None = None) -> tuple[Tensor, tuple[Tensor, ...]]:
        if token_ids.ndim != 1:
            raise ValueError("step expects token ids shaped [batch]")
        token = self.embedding(token_ids)
        if state is None:
            state = self.empty_state(token.shape[0], device=token.device, dtype=token.dtype)
        if len(state) != len(self.blocks):
            raise ValueError("state layer count does not match model")
        next_states = []
        for block, block_state in zip(self.blocks, state):
            token, block_state = block.step(token, block_state)
            next_states.append(block_state)
        token = self.final_norm(token)
        logits = F.linear(token, self.embedding.weight, self.output_bias)
        return logits, tuple(next_states)

    def forward(self, token_ids: Tensor, state: tuple[Tensor, ...] | None = None) -> tuple[Tensor, tuple[Tensor, ...]]:
        if token_ids.ndim != 2:
            raise ValueError("forward expects token ids shaped [batch, sequence]")
        if token_ids.shape[1] > self.config.context:
            raise ValueError("sequence exceeds configured context")
        outputs = []
        current = state
        for position in range(token_ids.shape[1]):
            logits, current = self.step(token_ids[:, position], current)
            outputs.append(logits)
        return torch.stack(outputs, dim=1), current

    def parameter_report(self) -> dict[str, int]:
        total = sum(parameter.numel() for parameter in self.parameters())
        embedding = self.embedding.weight.numel()
        return {"total": total, "embedding_tied": embedding, "core": total - embedding}
