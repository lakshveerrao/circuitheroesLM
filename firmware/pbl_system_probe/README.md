# PBL system probe

The smallest PBL firmware example. It prints chip, flash, internal heap and
PSRAM information, followed by a one-second serial heartbeat. It intentionally
has no board-specific peripheral dependency and is a useful starting point for
new ESP-IDF ports.

Run it from the repository root:

```sh
pbl run chip-information
```
