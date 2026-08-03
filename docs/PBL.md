# PBL product guide

PBL means **Pocket Board Lab**. It makes CircuitHeroesLM feel like a terminal
application instead of a collection of long build commands.

## First minute

From the repository root:

```sh
./pbl doctor
./pbl configure
./pbl
```

The first command checks the development environment, the second saves a local
hardware profile, and the third opens the full-screen menu. PBL stores local
preferences and generated builds under `.pbl/`; these files are not committed.

No Python package installer is used. The only product requirement is Python
3.9 or newer. Firmware compilation still requires ESP-IDF because PBL is a
safe interface to the real Espressif compiler and flashing tools, not a fake
replacement for them.

## Commands

| Command | Result |
| --- | --- |
| `pbl` | Open the terminal dashboard |
| `pbl help` / `pbl --help` | Show concise help |
| `pbl configure` | Choose processor and peripherals |
| `pbl configure --show` | Show the saved profile |
| `pbl detect-port` | Find likely connected ESP serial ports |
| `pbl test-codes` | Show examples and compatibility |
| `pbl select TEST` | Save the default example |
| `pbl build [TEST]` | Compile, without touching the device |
| `pbl upload [TEST]` | Incrementally build and flash |
| `pbl monitor [TEST]` | Open the serial monitor |
| `pbl run [TEST]` | Build, flash, and monitor |
| `pbl doctor` | Check tools, ports and profile |
| `pbl install` | Add a user-local command link; no pip or sudo |

`--dry-run` prints the exact underlying commands. `--force` is required to
override a hardware-profile mismatch. `pbl run` confirms before replacing
device firmware unless `--yes` is supplied. Installation also creates compact
aliases including `pbl--help`, `pbl--run`, `pbl--upload`,
`pbl--detect-port`, `pbl--test-codes`, `pbl--select`, and `pbl--configure`.

## Hardware profiles

The configurator separates six choices: processor, board, display, input,
microphone and speaker. This is deliberate. Two projects can use the same
processor while requiring completely different display buses, audio codecs or
touch controllers.

The first fully validated product profile is:

```text
processor   ESP32-S3
board       Waveshare ESP32-S3-Touch-AMOLED-1.8 (automatic revision)
display     368 x 448 AMOLED touch
input       capacitive touch
microphone  onboard input through ES8311
speaker     onboard ES8311 output
```

Other selections are present so ports have a stable configuration contract.
They do not imply that every listed peripheral driver is implemented today;
the test catalog clearly labels compatible examples.

## Safety and recovery

- Speaker tests remain silent until tapped and use a conservative output
  level. No continuous beep is generated.
- Voice recordings stay in volatile RAM, are played once, and are freed.
- PBL asks before a combined run overwrites device firmware.
- If ESP-IDF leaves an incomplete build directory, PBL moves it into
  `.pbl/recovered-builds` rather than deleting it.
- The native AI test automatically writes its matching CHLM artifact to the
  model partition after flashing the application.

## Adding a test code

Add an ESP-IDF project under `firmware/`, then register it in
`pbl_cli/test_codes.json`. Each record declares its ID, display name, hardware
summary, project path, supported processors and supported boards. A project may
also declare a numeric build mode or a model artifact and flash address.

Run the dependency-free regression suite with:

```sh
python3 -m unittest discover -s tests -p 'test_pbl_cli.py' -v
```
