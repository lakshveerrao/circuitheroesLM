# PBL internals

PBL (Pocket Board Lab) is deliberately implemented with the Python standard
library. It does not require a `pip install`, UV environment, Rich, or Textual.
The repository-root `pbl` executable owns the terminal UI and delegates builds
to the user's existing ESP-IDF installation.

`test_codes.json` is the user-visible test registry. Every runnable entry names
an ESP-IDF project, supported processors and boards, and any build-time mode or
model-partition payload. Tests that do not match the saved hardware profile are
shown but blocked unless the user deliberately supplies `--force`.
