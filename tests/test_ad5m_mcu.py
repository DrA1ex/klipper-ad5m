# Observable contracts of the AD5M firmware build and v0.11 wire protocol.
#
# Copyright (C) 2026, Alexander K <https://github.com/drA1ex>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'klippy'))
import msgproto


class AD5MBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='ad5m-mcu-tests-')
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.work = Path(cls.temporary.name)
        cls.development_files = {}
        for path in (ROOT / '.config', ROOT / 'out' / 'klipper.bin'):
            cls.development_files[path] = path.read_bytes() if path.exists() else None
        cls.outputs = {}
        for profile in ('eboard-n32g455', 'stm32f103xe'):
            output = cls.work / profile
            result = cls.invoke(profile, output)
            if result.returncode:
                raise AssertionError(result.stdout)
            cls.outputs[profile] = output

    @classmethod
    def invoke(cls, profile, output, env=None):
        return subprocess.run([sys.executable, str(ROOT / 'scripts/build-ad5m-mcu.py'), profile,
                               '--output', str(output)], env=env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def test_image_vectors_and_serial_transport(self):
        for profile, address, ram_end, clock in (
                ('eboard-n32g455', 0x08010000, 0x20020000, 144000000),
                ('stm32f103xe', 0x08000000, 0x20010000, 72000000)):
            with self.subTest(profile=profile):
                output = self.outputs[profile]
                image = (output / 'klipper.bin').read_bytes()
                stack, reset = struct.unpack_from('<II', image)
                self.assertEqual(stack, ram_end)
                self.assertEqual(reset & 1, 1)
                self.assertTrue(address <= reset - 1 < address + len(image))
                parser = msgproto.MessageParser()
                parser.process_identify((output / 'klipper.dict').read_bytes(), decompress=False)
                self.assertEqual(parser.get_constant_int('CLOCK_FREQ'), clock)
                self.assertEqual(parser.get_constant_int('SERIAL_BAUD'), 230400)
                self.assertEqual(parser.get_constant('RESERVE_PINS_serial'), 'PA10,PA9')

    def test_host_can_encode_analog_queries_and_look_up_motion_contracts(self):
        for profile, output in self.outputs.items():
            with self.subTest(profile=profile):
                parser = msgproto.MessageParser()
                parser.process_identify((output / 'klipper.dict').read_bytes(), decompress=False)
                for command in (
                        'config_analog_in oid=0 pin=PA0',
                        'query_analog_in oid=0 clock=100000 sample_ticks=1000 sample_count=8'
                        ' rest_ticks=100000 min_value=0 max_value=32760 range_check_count=4',
                        'queue_step oid=1 interval=10000 count=10 add=0',
                        'reset'):
                    self.assertTrue(parser.create_command(command))
                parser.lookup_command('analog_in_state oid=%c next_clock=%u value=%hu')
                parser.lookup_command('trsync_start oid=%c report_clock=%u report_ticks=%u expire_reason=%c')
                parser.lookup_command('trsync_trigger oid=%c reason=%c')

    def test_checksums_and_source_identity(self):
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        for profile, output in self.outputs.items():
            with self.subTest(profile=profile):
                metadata = json.loads((output / 'build-info.json').read_text())
                dictionary = json.loads((output / 'klipper.dict').read_text())
                self.assertEqual(metadata['source_commit'], commit)
                self.assertEqual(metadata['version'], dictionary['version'])
                self.assertEqual(metadata['commands'], len(dictionary['commands']))
                for line in (output / 'SHA256SUMS').read_text().splitlines():
                    expected, name = line.split(maxsplit=1)
                    self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), expected)

    def test_existing_output_is_preserved(self):
        output = self.work / 'existing'
        output.mkdir()
        marker = output / 'keep.txt'
        marker.write_text('keep')
        result = self.invoke('stm32f103xe', output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Output already exists', result.stdout)
        self.assertEqual(marker.read_text(), 'keep')

    def test_development_configuration_and_output_are_preserved(self):
        for path, original in self.development_files.items():
            with self.subTest(path=path.name):
                self.assertEqual(path.read_bytes() if path.exists() else None, original)

    def test_missing_toolchain_publishes_no_output(self):
        output = self.work / 'missing-compiler'
        result = self.invoke('stm32f103xe', output, dict(os.environ, CROSS_PREFIX='ad5m-missing-'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Missing tool', result.stdout)
        self.assertFalse(output.exists())

    def test_failed_compiler_publishes_no_partial_bundle(self):
        tools = self.work / 'broken-toolchain'
        tools.mkdir()
        for name in ('gcc', 'as', 'ld', 'objcopy', 'objdump', 'strip', 'cpp', 'readelf', 'size'):
            tool = tools / ('broken-' + name)
            tool.write_text('#!/bin/sh\nif [ "$1" = "--version" ]; then\n'
                            '    echo "broken toolchain"\n    exit 0\nfi\nexit 1\n')
            tool.chmod(0o755)
        output = self.work / 'compiler-failure'
        result = self.invoke('stm32f103xe', output, dict(os.environ, CROSS_PREFIX=str(tools / 'broken-')))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())

    def test_unknown_profile_publishes_no_output(self):
        output = self.work / 'unknown'
        result = self.invoke('mainboard-n32g455', output)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
