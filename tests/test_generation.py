from circuitheroeslm.generation import greedy_generate, render_fact_tape
from circuitheroeslm.model import ESRConfig, EngineeringStateRouterLM
from circuitheroeslm.tokenizer import EngineeringTokenizer


def test_greedy_generation_is_deterministic():
    tokenizer = EngineeringTokenizer.train(["resistor limits current"] * 8, 290)
    model = EngineeringStateRouterLM(ESRConfig(vocab_size=tokenizer.vocab_size, width=24, layers=2,
                                               lanes=4, state_width=8, mixer_width=40, context=32))
    fields = {name: "fact" for name in ("name", "family", "purpose", "symbol", "behavior", "constraint")}
    first = greedy_generate(model, tokenizer, "resistor", 5, fields)
    second = greedy_generate(model, tokenizer, "resistor", 5, fields)
    assert first == second


def test_fact_tape_inserts_exact_engineering_fields():
    tokenizer = EngineeringTokenizer.train(["Use <copy_name>: <copy_constraint>."] * 8, 300)
    tokens = tokenizer.encode("Use <copy_name>: <copy_constraint>.")
    rendered = render_fact_tape(tokens, tokenizer, {"name": "Tantalum capacitor", "constraint": "observe polarity"})
    assert rendered == "Use Tantalum capacitor: observe polarity."
