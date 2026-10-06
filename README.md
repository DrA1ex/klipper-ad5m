# AD5M MCU sources (`mcu-v0.11`)

This branch contains the recovered v0.11-era AD5M extruder-board firmware
sources, plus an STM32F103xE build profile for the replacement described in
[Forge-X discussion #94](https://github.com/DrA1ex/ff5m/discussions/94).

- [Build firmware](docs/AD5M_MCU_BUILD.md): prerequisites, profiles, commands,
  output files, and the limits of the STM32 replacement build.
- [Source and patch history](openwiki/ad5m-mcu-provenance.md): original Klipper
  commits, the eight recovered patches, and historical validation.
- [`main`](https://github.com/DrA1ex/klipper-ad5m/tree/main) records Forge-X's
  **host** patches. This MCU branch does not replace that host installation.

The recovered hardware tests cover the N32G455 extruder board. The STM32F103xE
profile is an offline build with the standard v0.11 protocol; it has not been
tested on a replacement mainboard and does not provide proprietary sensor
firmware. The build script never contacts or flashes a printer.

## Upstream Klipper

Welcome to the Klipper project!

[![Klipper](docs/img/klipper-logo-small.png)](https://www.klipper3d.org/)

https://www.klipper3d.org/

Klipper is a 3d-Printer firmware. It combines the power of a general
purpose computer with one or more micro-controllers. See the
[features document](https://www.klipper3d.org/Features.html) for more
information on why you should use Klipper.

To begin using Klipper start by
[installing](https://www.klipper3d.org/Installation.html) it.

Klipper is Free Software. See the [license](COPYING) or read the
[documentation](https://www.klipper3d.org/Overview.html). We depend on
the generous support from our
[sponsors](https://www.klipper3d.org/Sponsors.html).
