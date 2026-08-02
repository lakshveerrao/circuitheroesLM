# ESP32-S3 native probe

This ESP-IDF project verifies the exact CHLM artifact on hardware. It maps the
model partition, validates all bounds and CRCs, compares 100 sequences against
embedded golden logits, checks heap stability, then performs native CHTK
tokenization and a complete grounded generation.

Requirements: ESP-IDF 5.5.x, ESP32-S3 with 16 MB flash and 8 MB octal PSRAM.

```sh
idf.py -B build-native build
idf.py -B build-native -p /dev/cu.usbmodem1101 flash
esptool.py --chip esp32s3 --port /dev/cu.usbmodem1101 --baud 921600 \
  write_flash 0x310000 ../../models/native-esr-ple-v0.4/model.chlm
idf.py -B build-native -p /dev/cu.usbmodem1101 monitor
```

Replace the serial port when necessary. The final success marker is
`CIRCUITHEROESLM_NATIVE_DEVICE_PASS`. This probe overwrites the current device
application and partition table; it is a numerical/generation test firmware,
not the Circuit Heroes display UI.

`main/golden.bin` must come from the same model directory as the CHLM artifact
before building. The checked-in probe currently targets v0.4. To retest v0.3,
copy its golden file into that path, rebuild, and flash its model artifact.
