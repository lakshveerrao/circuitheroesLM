# pbl-lm

**PBL means Projects by Laksh.**

Install the CircuitHeroesLM hardware and local-AI terminal:

```sh
pip install pbl-lm
pbl
```

PBL provides an arrow-key terminal for board detection, hardware profiles,
display/touch/microphone/speaker tests, firmware upload, serial monitoring and
the circuitheroesLM native ESP32-S3 pilot.

PBL 0.3 adds **Import Git test code**. Paste a public HTTPS Git link and PBL
shallow-clones it, verifies repository limits, paths, symbolic links, ESP-IDF
structure and risky build hooks, matches it to the chosen processor, board and
display, and registers the exact verified commit as a selectable third-party
test.

- no Git clone;
- no UV environment;
- no Arduino CLI;
- no manual file copying;
- macOS, Linux, Windows and Ubuntu Touch launcher support;
- dependency-free Python launcher;
- version-matched official payload on first use.

The first `pbl` launch transfers the immutable PBL release associated with the
installed package version. Later launches use the local cached copy.

Researchers who also want the Python model-development dependencies can use
`pip install "pbl-lm[model]"`. They are intentionally not required by the
lightweight PBL hardware terminal.

Project and measured model results:
[github.com/lakshveerrao/circuitheroesLM](https://github.com/lakshveerrao/circuitheroesLM)
