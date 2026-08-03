# PBL Waveshare hardware laboratory

This is the visual and voice example behind PBL's Waveshare tests. One source
project exposes focused build modes for:

- AMOLED colors and alignment;
- full-panel capacitive touch tracking;
- a tap-initiated, low-volume speaker test;
- a live onboard microphone meter;
- three-second local record and one-time playback;
- an agent UI hardware bridge;
- I2C/BSP status;
- SRAM and PSRAM health;
- the full interactive board lab.

The speaker never starts automatically and no tone is looped. Recordings stay
in volatile memory, are played once, and are freed immediately.

Use the product CLI rather than remembering CMake variables:

```sh
pbl test-codes
pbl select board-full-lab
pbl run
```
