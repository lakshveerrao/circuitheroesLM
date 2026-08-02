# Native C runtime

`chlm.c` is the independently implemented reference runtime for the native ESR
and Engineering FactTape model. It loads CHLM v1, validates bounds and CRCs,
runs row-INT8 matrix/vector kernels, maintains fixed-size working/fact state,
and produces tied-embedding output logits.

Build and verify:

```sh
cc -std=c11 -O3 -Wall -Wextra -Werror \
  native_runtime/chlm.c native_runtime/host_verify.c -lm -o /tmp/chlm-verify
/tmp/chlm-verify models/native-esr-facttape-v0.3/model.chlm \
  models/native-esr-facttape-v0.3/model.chlm.golden.bin
```

Expected maximum difference is below `1e-4`; the current optimized host result
is `2.38419e-6`. The code intentionally uses portable scalar kernels first.
ESP32-specific acceleration is added only after this reference remains green.
