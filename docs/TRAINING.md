# Training

## Reproducible stages

1. Import and validate licensed component facts.
2. Generate grounded tasks with the verified facts included in model context.
3. Split by component family.
4. Tokenize with the checked-in 4,096-token tokenizer.
5. Apply loss only to answer tokens; prompt/catalogue formatting is context,
   not a training objective.
6. Train with validation checkpointing and early stopping.
7. Quantize to group-wise INT4.
8. Compare C runtime logits against a PyTorch golden file.
9. Evaluate exact names, types, explanations, units, and hallucination rate.
10. Flash only a checkpoint that passes every release gate.

## Why the first experiment was rejected

The first experiment asked a 4.1M-parameter model to memorize thousands of
component facts. Its numerical validation improved, but qualitative tests
showed wrong component classes and invented descriptions. The next dataset
puts verified facts in context and trains the model to explain and reason over
them. See `BENCHMARKS.md`.

## Compute

Training may use Apple Metal, CUDA, or CPU. The training machine is not part of
the final product. Exported inference remains completely offline on-device.
