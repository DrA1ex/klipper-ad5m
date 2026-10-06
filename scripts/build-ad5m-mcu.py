#!/usr/bin/env python3
# Build the AD5M MCU profiles without changing the caller's configuration.
#
# Copyright (C) 2026, Alexander K <https://github.com/drA1ex>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile


def run(command, cwd, **kwargs):
    return subprocess.run(command, cwd=cwd, check=True, **kwargs)


def build(args):
    root = Path(__file__).resolve().parents[1]
    output = Path(args.output or root / 'mcu-build' / args.profile).resolve()
    if output.exists():
        raise ValueError('Output already exists; select a new directory: %s' % output)

    # The firmware version and source archive must describe the same commit.
    run(['git', 'diff', '--exit-code', 'HEAD', '--', 'Makefile', 'src', 'lib',
         'scripts', 'klippy', 'config/ad5m'], root, stdout=subprocess.DEVNULL)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    version = subprocess.check_output(['git', 'describe', '--always', '--tags', '--long'],
                                      cwd=root, text=True).strip()
    prefix = os.environ.get('CROSS_PREFIX', 'arm-none-eabi-')
    tools = {}
    for name in ('gcc', 'as', 'ld', 'objcopy', 'objdump', 'strip', 'cpp', 'readelf', 'size'):
        tool = shutil.which(prefix + name)
        if tool is None:
            raise ValueError('Missing tool: %s%s; add Arm GNU Toolchain bin to PATH' % (prefix, name))
        tools[name] = tool

    compiler = subprocess.check_output([tools['gcc'], '--version'], text=True).splitlines()[0]
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.ad5m-build-', dir=output.parent) as temporary:
        work = Path(temporary)
        source = work / 'source'
        run(['git', 'clone', '--quiet', '--shared', '--no-checkout', str(root), str(source)], root)
        run(['git', 'checkout', '--quiet', '--detach', commit], source)
        shutil.copyfile(source / 'config' / 'ad5m' / (args.profile + '.config'), source / '.config')

        # The v0.11 compiler check calls unprefixed readelf, including on macOS.
        bin_dir = work / 'bin'
        bin_dir.mkdir()
        (bin_dir / 'readelf').symlink_to(tools['readelf'])
        env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ.get('PATH', ''))
        make_args = ['PYTHON=' + sys.executable, 'CROSS_PREFIX=' + prefix, 'CPP=' + tools['cpp']]
        # Resolve the seed before Make selects a board and creates its include links.
        run([sys.executable, 'lib/kconfiglib/olddefconfig.py', 'src/Kconfig'], source, env=env)
        run(['make', '-j%d' % args.jobs] + make_args, source, env=env)
        run([tools['objcopy'], '-O', 'ihex', 'out/klipper.elf', 'out/klipper.hex'], source)

        # Check the actual dictionary using the same encoder as the v0.11 host.
        sys.path.insert(0, str(source / 'klippy'))
        import msgproto
        dictionary = (source / 'out' / 'klipper.dict').read_bytes()
        parser = msgproto.MessageParser()
        parser.process_identify(dictionary, decompress=False)
        if parser.get_version_info()[0] != version:
            raise ValueError('Firmware version does not match the selected source commit')
        parser.create_command('query_analog_in oid=0 clock=100000 sample_ticks=1000 sample_count=8'
                              ' rest_ticks=100000 min_value=0 max_value=32760 range_check_count=4')
        constants = parser.get_constants()
        expected_clock = 144000000 if args.profile == 'eboard-n32g455' else 72000000
        if constants['SERIAL_BAUD'] != 230400 or constants['CLOCK_FREQ'] != expected_clock:
            raise ValueError('Unexpected clock or serial baud in the built firmware')
        if constants['RESERVE_PINS_serial'] != 'PA10,PA9':
            raise ValueError('Unexpected serial pins in the built firmware')
        image = (source / 'out' / 'klipper.bin').read_bytes()
        stack, reset = struct.unpack_from('<II', image)
        start = 0x08010000 if args.profile == 'eboard-n32g455' else 0x08000000
        ram_end = 0x20020000 if args.profile == 'eboard-n32g455' else 0x20010000
        if stack != ram_end or not reset & 1 or not start <= reset - 1 < start + len(image):
            raise ValueError('Unexpected stack or reset vector in the built firmware')

        artifacts = work / 'artifacts'
        artifacts.mkdir()
        for name in ('klipper.bin', 'klipper.hex', 'klipper.elf', 'klipper.dict'):
            shutil.copyfile(source / 'out' / name, artifacts / name)
        shutil.copyfile(source / '.config', artifacts / 'build.config')
        metadata = dict(profile=args.profile, source_commit=commit, version=version, compiler=compiler,
                        flash_address='0x%08x' % start, commands=len(json.loads(dictionary)['commands']),
                        responses=len(json.loads(dictionary)['responses']))
        (artifacts / 'build-info.json').write_text(json.dumps(metadata, indent=2) + '\n')
        manifest = ''.join('%s  %s\n' % (hashlib.sha256(path.read_bytes()).hexdigest(), path.name)
                           for path in sorted(artifacts.iterdir()))
        (artifacts / 'SHA256SUMS').write_text(manifest)
        run([tools['size'], str(artifacts / 'klipper.elf')], root)
        # Publish complete artifacts only; a failed build leaves no output bundle.
        if output.exists():
            raise ValueError('Output appeared during the build: %s' % output)
        artifacts.rename(output)
    print('Built %s at %s\nSource commit: %s' % (args.profile, output, commit))


def main():
    parser = argparse.ArgumentParser(description=__doc__ or 'Build AD5M MCU firmware locally; never flash a device.')
    parser.add_argument('profile', choices=('eboard-n32g455', 'stm32f103xe'))
    parser.add_argument('--output', help='New output directory (default: mcu-build/PROFILE)')
    parser.add_argument('--jobs', type=int, default=min(8, os.cpu_count() or 1))
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    try:
        build(args)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, 'Build failed: %s\n' % error)


if __name__ == '__main__':
    main()
