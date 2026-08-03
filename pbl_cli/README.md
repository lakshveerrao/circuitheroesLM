# PBL internals

PBL means **Projects by Laksh**. It is deliberately implemented with the Python standard
library. It does not require a `pip install`, UV environment, Rich, or Textual.
The repository-root `pbl` executable owns the terminal UI and presents friendly
firmware actions rather than raw compiler and flashing commands.

`test_codes.json` is the user-visible test registry. Every runnable entry names
an embedded firmware project, supported processors and boards, and any build-time mode or
model-partition payload. Tests that do not match the saved hardware profile are
shown but blocked unless the user deliberately supplies `--force`.
