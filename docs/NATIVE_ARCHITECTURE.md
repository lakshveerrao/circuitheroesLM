# Native architecture: Engineering State Router

## Design objective

Engineering State Router (ESR) is a small, sequential decoder designed around
ESP32 constraints: fixed-size recurrent state, predictable memory access, no
KV cache, no per-layer vocabulary table, and no attention matrix. It is a new
project implementation and model format, not the prototype PLE runtime.

## Token path

For token `t`, embedding `x_t` enters each ESR layer. A layer owns four state
lanes intended to specialize during supervised training:

1. entity/component identity;
2. relation/connectivity;
3. quantity/unit;
4. constraint/behavior.

For lane `k`, with previous state `s` and normalized input `x`:

```text
proposal = tanh(input_projection_k(x) + recurrent_scale_k * s)
write    = sigmoid(write_projection_k(x) + write_bias_k)
s_new    = s + write * (proposal - s)
```

A softmax router weights the four updated states. Their routed concatenation is
projected back to model width and added residually. A compact gated channel
mixer then transforms the result:

```text
mixed = down(silu(gate(x)) * value(x))
x_new = x + state_output + mixed
```

Each layer keeps only `4 * state_width` recurrent values. Generation cost and
state memory do not grow with context length.

## Grounded engineering memory

Exact names, pin facts, ratings, units, and connection constraints are stored
as attributed local fact cards. Retrieval is deterministic and outside the
neural weights. Fact cards are serialized into the prompt using explicit
fields. The model learns explanation and relation language; it is not expected
to guess absent datasheet facts.

## Pilot configuration

| Field | Initial value |
| --- | ---: |
| Vocabulary | 1,536 engineering byte-BPE tokens |
| Model width | 96 |
| ESR layers | 4 |
| State lanes | 4 |
| State width per lane | 32 |
| Channel mixer | 192 |
| Context | 128 tokens |
| Initialization | random |

These values are candidates, not release claims. Candidate selection depends
on factuality, unseen-family evaluation, quantized quality, and device speed.

## Native inference format

The format will use magic `CHLM`, an explicit version, endian marker, tensor
directory, dimensions, quantization descriptors, offsets, lengths, CRC32, and
whole-file SHA-256. Unknown versions and invalid bounds must fail closed.

The first reference export uses row-wise INT8 to establish correctness. INT4
is introduced only after float/INT8 host and device goldens agree.

## Engineering release gates

- component/type identity at least 95% on the declared pilot domain;
- pin, polarity, unit, and constraint rubric at least 90%;
- unsupported factual claims below 2% after verifier intervention;
- held-out component-family results reported separately;
- 100 consecutive device generations without crash or memory growth;
- zero network calls in the firmware demonstration;
- source audit passes the originality policy.

