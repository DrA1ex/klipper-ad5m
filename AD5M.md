# Klipper for the Adventurer 5M: what Forge-X changes

This repository is a copy of [Klipper](https://github.com/Klipper3d/klipper)
with one purpose: to show, as ordinary Git history, how the host-side Klipper
that [Forge-X](https://github.com/DrA1ex/ff5m) installs on the FlashForge
Adventurer 5M / 5M Pro differs from upstream Klipper and from the stock
FlashForge Klipper.

It is not a new Klipper distribution and it is not meant to be installed. The
Forge-X repository (`ff5m`) stays the place where the files are shipped from.
This repository is the readable record of what is in them.

## The history

```text
v0.11.0                      upstream Klipper release, e02b7256
  |
  +-- FlashForge: stock changes ...      what the stock printer firmware changes
  |
  +-- Forge-X commits                    one topic per commit, in a fixed order
```

- **Base.** Upstream Klipper `v0.11.0` (`e02b725602067a2cd098a62be9a4bb10fc74a9bd`).
  The stock FlashForge host Klipper is from that release. Of the 175 files
  under `klippy/` in the stock firmware, 169 are byte-identical to `v0.11.0`.
- **Stock changes.** The first commit after `v0.11.0` (`182e96ab8394201923e095ede450f2468f293d16`) contains the
  changes FlashForge made to four of the six files that differ.
- **Forge-X commits.** Everything after that. Each commit has a message that
  says what it changes and why, and names the upstream commit it is based on,
  if there is one.

Compare views:

- everything Forge-X changes compared with the stock firmware:
  [`182e96ab83...main`](../../compare/182e96ab8394201923e095ede450f2468f293d16...main)
- everything compared with upstream Klipper:
  [`e02b7256...main`](../../compare/e02b725602067a2cd098a62be9a4bb10fc74a9bd...main)

## Three kinds of commits

1. **Cherry-picks.** Upstream commits that apply to the `v0.11.0` code are
   cherry-picked with `-x`. The original author is kept, and the message ends
   with `(cherry picked from commit ...)`.
2. **Backports written by hand.** Many upstream fixes are written for much newer
   Klipper code (for example `toolhead.py` and `probe.py` were reworked since
   `v0.11.0`), so they cannot be cherry-picked. Those commits say so, name the
   upstream commit, and list the differences from it. The author of those
   commits is the person who adapted the change.
3. **Forge-X changes.** Changes that have no upstream counterpart, such as the
   `tune_klipper` lookahead setting, the extra logging in `homing.py` and
   `mcu.py`, or the `temperature_sensor` trigger. The message explains the
   change. Where the original reason was not recorded, the message says that.

## What this history is, and is not

The Forge-X patches were developed as whole files, not as a series of commits
on top of Klipper. This history was therefore **reconstructed by topic** after
the fact. The order and the grouping are chosen to be easy to read; they are
not the order in which the work was done, and individual commits were not
tested one by one on a printer.

What is exact, and can be checked:

- the final tree: every file under `klippy/` that Forge-X replaces is
  byte-identical to the file Forge-X ships (see below);
- the stock commit: the four files it contains have exactly the MD5 sums of the
  stock firmware (the `md5sum.list` that Forge-X uses for its file check):

  | File | MD5 |
  | --- | --- |
  | `klippy/toolhead.py` | `b82b6956297f9fc15041a1d286a72aa8` |
  | `klippy/extras/tmc.py` | `51050bbd49019ed3a239e9c75671cedf` |
  | `klippy/queuelogger.py` | `5fb05a43095c4cb3848cb0ea3ce37dc4` |
  | `klippy/chelper/__init__.py` | `7095fcf9f001816dec7218daac523d8f` |

The original FlashForge sources are not public, so the stock commit is a
reconstruction that matches those hashes.

## Open points

- `klippy/extras/virtual_sdcard.py`. The stock file list has the MD5
  `025354a1c2b767f849e9262a37a786fd`, which does not match any upstream
  version. A copy of the file from a printer is identical to upstream
  `v0.11.0`. The stock change to this file, if there is one, is not
  reconstructed. Until that is resolved, the stock commit leaves the file as
  upstream.
- `klippy/chelper/c_helper.so` is a binary built from the C sources in
  `klippy/chelper/`. The stock library is built from the unmodified `v0.11.0`
  sources. The Forge-X library is built from the sources in this tree, which
  differ from `v0.11.0` in `kin_extruder.c` (dynamic pressure advance,
  upstream commit `c84d78f3`).
- A few Forge-X changes have no recorded motivation. Their commit messages say
  so (`toolhead: lower the default buffer_time_high`, `tmc: run the driver
  checks again when enabling`, `gcode: change how commands from the G-code pipe
  are processed`).

## How the files map to Forge-X

| This repository | Forge-X repository |
| --- | --- |
| `klippy/<path>.py` | `.py/klipper/patches/<path>.py` |

Forge-X installs the files from `.py/klipper/patches/` over the stock files in
`/opt/klipper/klippy/` (the stock file is kept as `<file>.bak`). The Forge-X
repository contains a manifest with the SHA-256 of each file and a test that
checks the shipped files against it. The list of changes, with upstream links,
is in the Forge-X document
[Klipper fixes and AD5M-specific hardening](https://github.com/DrA1ex/ff5m/blob/main/docs/KLIPPER.md).

Forge-X plugins (`.py/klipper/plugins/`) add new files; they do not replace
Klipper modules and are not part of this repository, except
`gcode_shell_command.py`, which is shipped in `patches/`.

## License

Klipper is licensed under the GNU GPLv3, and so are all changes here. See
`COPYING`.
