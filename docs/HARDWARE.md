# Hardware support

## Capability tiers

| Tier | Minimum practical memory | Intended behavior |
| --- | --- | --- |
| Full | 16 MiB flash, 8 MiB PSRAM | Generative model, catalogue, UI, audio |
| Compact | 4–8 MiB flash, at least 2 MiB PSRAM | Smaller model, reduced context/UI |
| Micro | 4 MiB flash, no PSRAM | Retrieval/classification, not full generation |

The Waveshare ESP32-S3 Touch AMOLED 1.8 is the tested reference board. Generic
ESP profiles define capability contracts; they are not claims of physical
testing. ESP32-P4 support remains provisional until tested on a real board.

`esp32-s31` is not an Espressif target and is rejected by configuration.

Displays, touch controllers, microphones, speakers, and codecs are adapters.
They can change without retraining or modifying the model runtime.
