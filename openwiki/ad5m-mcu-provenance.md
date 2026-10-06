# AD5M MCU source provenance and engineering notes

## Recovered source history

The MCU branch restores the locally preserved eboard source series over
upstream Klipper
[`c54d83c9f134d47f00da5ecd0d762e01748aaa59`](https://github.com/Klipper3d/klipper/commit/c54d83c9f134d47f00da5ecd0d762e01748aaa59)
(2023-03-15, v0.11 era). This differs from the host-history base on `main`,
which is the v0.11.0 release. Keeping a separate MCU branch preserves both
histories without combining a host reconstruction with a different MCU base.

The eight commits were recovered from the author's local August 2026 eboard
bundle, retaining their original author, committer, and dates. Applying them
reproduced the exact original HEAD
`14c7b7d09b62e857d34a652b0cdc1413808e6661`. No printer logs, deployment
wrappers, stock binaries, or local workflow files are published in this tree.

| Recovered commit | Change | Verified original source |
| --- | --- | --- |
| `35b814fdf3e29a06c19754be8e91cfc8d02abfa4` | N32G45x MCU/library support | [Klipper `23e82d37`](https://github.com/Klipper3d/klipper/commit/23e82d37f14b79a164234361a01b893443b5a34d); only `src/` and `lib/`, excluding the Voxelab printer configuration |
| `d37f84ea368bcd08f15b339b745eb9a95b8fd169` | STM32F1 conditions in PWM/USB code | [Klipper `ecc23fc6`](https://github.com/Klipper3d/klipper/commit/ecc23fc6fa3c3a866cf8dbbb0a118adbe7e61568) |
| `fe7e2c744755111a79e554a09759db6308a0ae69` | Timer/task arbitration | [Klipper `ea546c78`](https://github.com/Klipper3d/klipper/commit/ea546c789b4d1278078187b386ba85f324267892) |
| `e8a7285581fde30480a2b1a3fb39b4b81620130a` | N32G455 eboard clock, RAM, boot offset | Local hardware configuration, checked against Factory firmware and the xblax eboard profile |
| `5b13b29ec4e6b4fca645ca775442238ff0868c2c` | Modern Arm GCC/newlib linking | STM32-relevant subset of [Klipper `ae227d48`](https://github.com/Klipper3d/klipper/commit/ae227d485cdac859b22d77da4072f870bce07740) |
| `334beffb06c6bd50e04828a6de46112f0ec45c58` | FlashForge eboard reset lifecycle | Adapted against [xblax `c349aad8`](https://github.com/xblax/klipper/commit/c349aad85788649843f62187432298b7abce3b44) and [xblax `245ec843`](https://github.com/xblax/klipper/commit/245ec843c4a4a7a7137df3c62852265213695d91); behavior independently checked against Factory HEX |
| `d1febf9cbd389561b2f3c87aa0446204523a64a9` | N32 ADC PA0 mapping | [Klipper `3a11645a`](https://github.com/Klipper3d/klipper/commit/3a11645afeaf5573a0f244a65c8533a513799395) |
| `14c7b7d09b62e857d34a652b0cdc1413808e6661` | Eboard PB7 heater power gate | Locally written; pin assignment identified in xblax configuration and independently tested on the eboard |

For patches 1 (`src/` and `lib/` subset), 2, 3, and 7, `git patch-id --stable`
matches the verified original upstream diffs. The old local handoff had
incorrect upstream hashes for the first three. They are corrected above by
matching the actual patches to public upstream history, rather than copying
the old note's references.

## The small scheduler patch

Kevin O'Connor's upstream commit
[`ea546c789b4d1278078187b386ba85f324267892`](https://github.com/Klipper3d/klipper/commit/ea546c789b4d1278078187b386ba85f324267892),
dated 2024-10-21, is titled `sched: Improve timer vs task priority check`.
Its complete patch is the recovered commit `fe7e2c74`.

It replaces `sched_tasks_busy()` with `sched_check_set_tasks_busy()` and
requires activity across consecutive priority checks before timers yield to
tasks. Going idle clears the busy state. This reduces unnecessary task
interruptions between stepper timers, including simultaneous steppers on
the same rail during homing/probing.

It does **not** remove `Timer too close`, disable shutdown checks, or execute
a command before the host delivers it. The historical investigation involved
a late `queue_digital_out`; the patch was an experiment, not a demonstrated
fix for that print failure. There was no long print soak test in the recovered
validation record.

## Eboard-specific changes

The N32G455 eboard application runs at `0x08010000` after the stock 64 KiB
bootloader. Its clock is 144 MHz from a 12 MHz crystal; RAM ends at
`0x20020000`. The old eboard hardware facts are preserved, rather than
generalizing this configuration into an arbitrary N32 board profile.

Normal Klipper `reset` writes `0x1234` to backup register DR1 to bypass the
FlashForge bootloader's serial update window. A bootloader request performs
a reset without that bypass. These paths apply only to N32G455 with the
64 KiB bootloader option. They do not change the no-bootloader STM32 profile.

`CONFIG_FLASHFORGE_AD5M_EBOARD` is off by default. The eboard profile enables
it to raise PB7 at startup and lower it on MCU shutdown. PA8 remains the
heater's PWM output. The gate's hardware assignment was identified in
xblax's host `[output_pin extruder_heater]` configuration. No MCU heater-gate
code was copied from xblax; the local implementation uses ordinary Klipper
GPIO, init, and shutdown primitives.

The ADC correction replaces placeholder zero pin entries with
`ADC_INVALID_PIN=0xFF`, preventing those placeholders from matching PA0.
Without it, the historical first N32 build reported an invalid nozzle
temperature and was rolled back.

## Historical validation and exact reproduction

The local record reports that `14c7b7d0` was flashed to the original N32 eboard
on 2026-08-27. A brief 40 C nozzle test and shutdown/restart check succeeded.
The recorded firmware had 75 commands, 28 responses, and a 26,748-byte BIN.
This is evidence about the original eboard, not the replacement STM32
mainboard. No live printer operation was performed when publishing this
source recovery.

To reproduce the historical runtime and version using Arm GNU 13.2.Rel1:

```sh
git clone --no-tags --branch mcu-v0.11 --single-branch https://github.com/DrA1ex/klipper-ad5m.git klipper-ad5m-historical
cd klipper-ad5m-historical
git checkout --detach 14c7b7d09b62e857d34a652b0cdc1413808e6661
cat > .config <<'EOF'
CONFIG_LOW_LEVEL_OPTIONS=y
CONFIG_MACH_STM32=y
CONFIG_MACH_N32G455=y
CONFIG_STM32_FLASH_START_10000=y
CONFIG_STM32_CLOCK_REF_12M=y
CONFIG_STM32_SERIAL_USART1=y
CONFIG_SERIAL_BAUD=230400
CONFIG_INITIAL_PINS=""
CONFIG_FLASHFORGE_AD5M_EBOARD=y
EOF
make olddefconfig
make clean
make -j4 CPP=arm-none-eabi-cpp
arm-none-eabi-objcopy -O ihex out/klipper.elf out/klipper.hex
```

The historical `scripts/check-gcc.sh` uses unprefixed `readelf`. On macOS,
provide GNU `readelf` or put a temporary symlink to `arm-none-eabi-readelf`
on `PATH` before running `make`; do not accept a check that reports missing
`readelf`. The current build script supplies that temporary link automatically.

Debug ELF bytes depend on the absolute build path. Compare flashed BIN/HEX
and dictionary using the same compiler and source version. Current profile
builds embed newer source commits and will have different artifact checksums.

The historical checkout had no tags, so `git describe` returned `14c7b7d0`.
The clone above deliberately uses `--no-tags`; with the v0.11.0 tag present,
the version becomes `v0.11.0-151-g14c7b7d0` and the firmware bytes differ.
During source publication, a clean no-tag checkout reproduced all three
preserved artifacts byte-for-byte:

| Artifact | SHA-256 |
| --- | --- |
| BIN, 26,748 bytes | `b8ba68d39a7164318da45d2a7ff77c168579688350be1cd4a6d809e6befb68ac` |
| HEX | `d3cc7a4db4b102bdb2f53654f3f1a029d0f4ab04ed6f4e0c9e1f9af5acddef96` |
| Dictionary | `079a4f0c1874bf2c7d71aa4a00a0ae3a9da8dbdb871e815e3c3a2676ae000855` |

## New build workflow and tests

The new STM32F103xE option selects 512 KiB flash and 64 KiB RAM; other F103
variants keep their previous defaults. The USART1, 12 MHz crystal and
no-bootloader settings come directly from discussion #94. This adds memory
configuration, not a reimplementation of FlashForge mainboard peripherals.

The build script owns one temporary local checkout. It observes Git and the
toolchain, builds one selected profile, checks the result, and publishes one
complete artifact directory. It refuses modified build inputs or an existing
output. Failed builds clean up the temporary checkout without publishing a
partial bundle. It leaves the caller's `.config` and `out/` alone.

Run the repository's MCU tests with a complete Arm toolchain on `PATH`:

```sh
python3 -m venv .venv
.venv/bin/python -m unittest discover -s tests
```

The tests execute both real cross-builds and check firmware vectors, serial
transport, source identity, checksums, actual v0.11 host command encoding,
and failure behavior for existing output, missing/failing tools, and unknown
profiles. There are no source-layout or configuration-text mirror tests.

The RFC boundary is intentionally small: preserve the recovered eboard
runtime, keep host history on `main`, make the two board choices visible,
and stop on build failures. Mainboard sensor reverse engineering, firmware
installation, live validation, and a host upgrade are separate work.
