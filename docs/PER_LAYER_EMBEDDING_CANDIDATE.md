# Per-layer embedding candidate

## Method attribution

Google describes Per-Layer Embeddings (PLE) in Gemma 3n as layer-specific
embedding parameters that can be generated or cached outside the core working
memory and added as layers execute:
<https://ai.google.dev/gemma/docs/gemma-3n>.

circuitheroesLM adapts the published PLE idea to the ESR architecture and its
CHLM microcontroller runtime. Google is credited for introducing the method in
the Gemma 3n documentation.

## ESP32 adaptation

For each token and ESR layer, one row from a layer-specific INT8 embedding table
is read from mapped flash and added before that layer. With four layers and
width 96, the reference path reads approximately 400 bytes per model step. The
recurrent ESR state and scratch buffers remain fixed-size in RAM. Baseline v0.3
remains available unchanged.

## v0.4 result

v0.4 improved best validation loss from 0.2801 to 0.263524 while retaining
864/864 float and 864/864 row-INT8 held-out passes. Its CHLM artifact is
1,229,312 bytes. Strict C, sanitizers, grounded host generation, and the
100-sequence device test passed. On ESP32-S3 it measured 39.45 ms/token versus
39.42 ms/token for v0.3, with unchanged heap before/after. The device/reference
maximum delta was `4.76837e-6`.

This makes v0.4 the best measured candidate, while v0.3 remains the smaller
baseline. Neither result justifies a claim of perfect or open-domain reasoning.
