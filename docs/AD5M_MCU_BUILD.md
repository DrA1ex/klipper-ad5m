# Building AD5M MCU firmware

Use the `mcu-v0.11` branch for MCU builds. The `main` branch records the
Forge-X host patches. These are different source histories; do not install
the MCU branch's `klippy/` over the Forge-X host.

## Choose the board

| Profile | Intended hardware | Crystal / CPU | UART | Application address |
| --- | --- | --- | --- | --- |
| `eboard-n32g455` | AD5M extruder board, original N32G455 and stock bootloader | 12 / 144 MHz | USART1 PA9/PA10, 230400 | `0x08010000` (64 KiB offset) |
| `stm32f103xe` | STM32F103xE family, including the replacement described in discussion #94 | 12 / 72 MHz | USART1 PA9/PA10, 230400 | `0x08000000` (no bootloader) |

The `stm32f103xe` profile selects `CONFIG_MACH_STM32F103xE=y` for the
STM32F103xE family with 512 KiB flash and 64 KiB RAM. It leaves SWD enabled and
does not enable the N32-only bootloader or extruder heater-gate behavior.
Its settings come from the request in
[discussion #94](https://github.com/DrA1ex/ff5m/discussions/94), rather than
measurements on the replacement board.

**The STM32 build is experimental.** A successful build and protocol check do
not establish that the replacement chip works with every mainboard peripheral
or that the stock mainboard firmware has been reproduced. The recovered
sources were built for the extruder board; they contain no proprietary
`trigger_analog` implementation. They also do not include the newer upstream
HX71x, ADS1220, or SOS-filter modules. Those are not added merely to make a
version label match. See the troubleshooting section below.

## Prerequisites

You need Git, GNU Make, Python 3, and a complete Arm GNU Toolchain for
`arm-none-eabi`, including newlib. The build uses Python's standard library;
no host Klipper Python dependencies are needed.

The recovered firmware was built with **Arm GNU Toolchain 13.2.Rel1**, GCC
13.2.1 and binutils 2.41. The same toolchain was used to verify both profiles
in this repository. Download the package matching your computer from
[Arm's official 13.2.Rel1 downloads](https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads/13-2-rel1).

On Apple Silicon, the package is
`arm-gnu-toolchain-13.2.Rel1-darwin-arm64-arm-none-eabi.tar.xz`.
Its SHA-256 is
`39c44f8af42695b7b871df42e346c09fee670ea8dfc11f17083e296ea2b0d279`.
Unpack it into a separate directory, then put its `bin` directory on `PATH`:

```sh
export PATH="/path/to/arm-gnu-toolchain/bin:$PATH"
arm-none-eabi-gcc --version
arm-none-eabi-gcc -print-file-name=libc.a
```

The second command must resolve to an existing library, not just `libc.a`.
On Ubuntu/Debian, `gcc-arm-none-eabi`, `binutils-arm-none-eabi`, and
`libnewlib-arm-none-eabi` provide the tools and libraries, but their versions
may differ from the historical toolchain.

## Build

```sh
git clone --branch mcu-v0.11 --single-branch https://github.com/DrA1ex/klipper-ad5m.git
cd klipper-ad5m

# Replacement STM32F103xE, without a bootloader:
python3 scripts/build-ad5m-mcu.py stm32f103xe

# Original extruder board, with its stock bootloader:
python3 scripts/build-ad5m-mcu.py eboard-n32g455
```

The script builds the committed source in a temporary local checkout. It
preserves your existing `.config` and `out/` and rejects uncommitted changes
to build inputs. It performs no downloads, printer connections, or flashing.
Commit build-input changes before using it, or use ordinary `make` for
development.

Results are written to `mcu-build/<profile>/` only after all steps succeed:

| File | Purpose |
| --- | --- |
| `klipper.bin` | Raw application firmware |
| `klipper.hex` | Intel HEX with the application address |
| `klipper.elf` | Linked firmware with debug symbols |
| `klipper.dict` | Exact MCU command dictionary for checking the host protocol |
| `build.config` | Fully resolved configuration used for this build |
| `build-info.json` | Source commit, compiler, version, address, and protocol counts |
| `SHA256SUMS` | Checksums of all files above |

An existing output directory is never overwritten. For another build, choose
a new directory:

```sh
python3 scripts/build-ad5m-mcu.py stm32f103xe --output ./mcu-build/stm32f103xe-second --jobs 4
```

The script checks the stack/reset vectors, UART pins and speed, CPU frequency,
firmware version, and encoding of the standard v0.11 `query_analog_in`
command. Save the dictionary and build metadata together with the binary.

`CROSS_PREFIX` can select a toolchain outside `PATH`, for example:

```sh
CROSS_PREFIX=/path/to/toolchain/bin/arm-none-eabi- python3 scripts/build-ad5m-mcu.py stm32f103xe
```

## Using the output

For the STM32 profile, the raw binary is linked for the address requested in
discussion #94: `0x08000000`. Use it only with that no-bootloader layout.
The eboard binary is linked for `0x08010000` and must preserve the original
bootloader. These images are not interchangeable.

This guide supplies builds, not an automatic firmware installer. The STM32
replacement still requires board-specific validation by its owner before
movement, heating, or printing. No STM32 hardware validation is claimed here.

## Troubleshooting discussion #94

`MCU Protocol error` is about missing commands or different parameter formats,
not equality of the host and MCU Git version strings. The reported
`Unable to encode: query_analog_in` is not enough to identify its cause.

In this source generation, the standard command lives in
[`src/adccmds.c`](../src/adccmds.c), with this complete wire format:

```text
query_analog_in oid=%c clock=%u sample_ticks=%u sample_count=%c rest_ticks=%u min_value=%hu max_value=%hu range_check_count=%c
```

The build verifies that the v0.11 host encoder accepts a query with all these
parameters. `trigger_analog` is not needed to define this command. If the
error persists, compare the actual MCU dictionary with the host's command
and keep the full error traceback. The dictionary of this build may still
lack additional commands required by a particular stock mainboard setup.

The recovered bundle only establishes an eboard implementation. A complete
replacement of proprietary mainboard sensor firmware requires its exact
command contracts and a separate implementation/validation effort. The
modern xblax FlashForge UART sensor drivers and upstream generic load-cell
drivers are not evidence that those contracts match Forge-X's stock host.

## Historical firmware

The exact recovered source chain ends at
[`14c7b7d0`](https://github.com/DrA1ex/klipper-ad5m/commit/14c7b7d09b62e857d34a652b0cdc1413808e6661).
New builds embed their current source commit and therefore need not have
the same checksum as the 2026-08-27 firmware, even when the eboard runtime
code is unchanged. Historical measurements, upstream links, and a recipe
to reproduce that exact build are in the
[source history](../openwiki/ad5m-mcu-provenance.md).
