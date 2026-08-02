import json
from pathlib import Path

from circuitheroeslm.tokenizer import EngineeringTokenizer
from tools.train_native import encode_row


def test_prompt_tokens_are_masked_from_loss():
    tokenizer = EngineeringTokenizer.train(["<fact> resistor <answer> limits current"] * 4, 290)
    row = {"prompt": "<fact> resistor <answer>", "answer": "limits current"}
    tokens, labels = encode_row(row, tokenizer, 128)
    first_answer = len([1] + tokenizer.encode(row["prompt"])) - 1
    assert labels[:first_answer] == [-100] * first_answer
    assert any(label >= 0 for label in labels[first_answer:])
    assert len(tokens) == len(labels)
