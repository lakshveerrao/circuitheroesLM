from pathlib import Path
import tempfile

from circuitheroeslm.tokenizer import EngineeringTokenizer


def test_round_trip_engineering_text():
    texts = ["10 kΩ resistor", "gate-to-source voltage", "5 V → 3.3 V"]
    tokenizer = EngineeringTokenizer.train(texts * 4, 300)
    for text in texts:
        assert tokenizer.decode(tokenizer.encode(text)) == text


def test_serialized_tokenizer_is_deterministic():
    texts = ["pin=GND voltage=0 V", "pin=VCC voltage=5 V"] * 5
    first = EngineeringTokenizer.train(texts, 290)
    second = EngineeringTokenizer.train(texts, 290)
    assert first.merges == second.merges
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "tokenizer.json"
        first.save(path)
        restored = EngineeringTokenizer.load(path)
        assert restored.encode(texts[0]) == first.encode(texts[0])


def test_engineering_segments_use_reserved_ids():
    tokenizer = EngineeringTokenizer.train(["<fact>name=resistor<ask>task=explain<answer>"] * 4, 290)
    tokens = tokenizer.encode("<fact>name=resistor<ask>task=explain<answer>")
    assert tokens[0] == 3
    assert 4 in tokens
    assert tokens[-1] == 5
