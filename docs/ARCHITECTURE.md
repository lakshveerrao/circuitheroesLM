# Architecture

## Product pipeline

Circuit Heroes LM separates knowledge, language generation, and hardware:

1. A local catalogue resolves the component and retrieves verified facts.
2. A structured prompt labels identity, family, description, package, and task.
3. A quantized decoder model creates a short learner-facing response.
4. A verifier rejects unsupported part names, units, pin claims, and limits.
5. Independent display and audio drivers present the same accepted response.

The model is not permitted to replace missing facts with confident guesses.

## Model family

The device model is a decoder-only transformer using:

- rotary position embeddings;
- RMS normalization;
- grouped-query-free multi-head causal attention;
- SwiGLU feed-forward blocks;
- Per-Layer Embeddings stored primarily in flash;
- tied input/output embeddings;
- group-wise INT4 weights with FP16 scales;
- optional INT8 activations for ESP32-S3 acceleration.

## Hardware reasoning representation

“Hardware thinking” is an observable, testable structured process—not a claim
that the chip thinks like a human. Training and inference use these fields:

```text
task | component | family/subtype | verified function | package/appearance |
symbol/pins when available | operating constraints when available | answer
```

Only the final short answer is shown to the learner. Internal fields are used
to ground generation and to verify it.

## Higher-compute path

The next experiment uses a larger 7M-class student and a teacher-distillation
pipeline. The teacher runs only during training. The exported student remains
fully local on the ESP32-S3. More training compute does not add a runtime cloud
dependency.
