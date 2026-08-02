from circuitheroeslm.generation import greedy_generate
from circuitheroeslm.model import ESRConfig, EngineeringStateRouterLM
from circuitheroeslm.tokenizer import EngineeringTokenizer


def test_greedy_generation_is_deterministic():
    tokenizer = EngineeringTokenizer.train(["resistor limits current"] * 8, 290)
    model = EngineeringStateRouterLM(ESRConfig(vocab_size=tokenizer.vocab_size, width=24, layers=2,
                                               lanes=4, state_width=8, mixer_width=40, context=32))
    first = greedy_generate(model, tokenizer, "resistor", 5)
    second = greedy_generate(model, tokenizer, "resistor", 5)
    assert first == second
