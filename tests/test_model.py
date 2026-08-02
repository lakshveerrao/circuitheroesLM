import torch

from circuitheroeslm import FORMAT_MAGIC, PROJECT_NAME
from circuitheroeslm.model import ESRConfig, EngineeringStateRouterLM


def tiny_config() -> ESRConfig:
    return ESRConfig(vocab_size=64, width=24, layers=2, lanes=4, state_width=8, mixer_width=40, context=16)


def test_exact_project_identity():
    assert PROJECT_NAME == "circuitheroesLM"
    assert FORMAT_MAGIC == b"CHLM"


def test_sequence_matches_incremental_steps():
    torch.manual_seed(7)
    model = EngineeringStateRouterLM(tiny_config()).eval()
    tokens = torch.tensor([[1, 4, 9, 2], [3, 8, 5, 7]])
    with torch.no_grad():
        sequence_logits, sequence_state = model(tokens)
        state = None
        incremental = []
        for position in range(tokens.shape[1]):
            logits, state = model.step(tokens[:, position], state)
            incremental.append(logits)
    assert torch.allclose(sequence_logits, torch.stack(incremental, dim=1), atol=1e-6)
    for expected, actual in zip(sequence_state, state):
        assert torch.allclose(expected, actual, atol=1e-6)


def test_state_is_constant_size_across_context():
    model = EngineeringStateRouterLM(tiny_config()).eval()
    _, short_state = model(torch.tensor([[1, 2]]))
    _, long_state = model(torch.tensor([[1, 2, 3, 4, 5, 6]]))
    assert [item.shape for item in short_state] == [item.shape for item in long_state]


def test_random_logits_have_healthy_scale():
    torch.manual_seed(11)
    model = EngineeringStateRouterLM(tiny_config()).eval()
    logits, _ = model(torch.tensor([[1, 2, 3]]))
    assert logits.abs().max().item() < 3.0


def test_rejects_invalid_shapes_and_context():
    model = EngineeringStateRouterLM(tiny_config())
    try:
        model(torch.ones(1, 17, dtype=torch.long))
    except ValueError as error:
        assert "context" in str(error)
    else:
        raise AssertionError("oversized context was accepted")
