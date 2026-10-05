#!/usr/bin/env python
# Small regression tests for the AD5M GC/status snapshot optimizations.
import copy
import gc
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "klippy"))

import configfile
from extras import garbage_collection


class FakePrinter:
    def __init__(self):
        self.handlers = {}
    def register_event_handler(self, event, callback):
        self.handlers[event] = callback


class FakeConfig:
    def __init__(self, printer):
        self.printer = printer
    def get_printer(self):
        return self.printer


def test_garbage_collection_lifecycle():
    calls = []
    original = {}
    missing = object()
    for name in ("collect", "freeze", "unfreeze"):
        original[name] = getattr(gc, name, missing)
    try:
        gc.collect = lambda generation=None: calls.append(
            ("collect", generation))
        gc.freeze = lambda: calls.append(("freeze", None))
        gc.unfreeze = lambda: calls.append(("unfreeze", None))

        printer = FakePrinter()
        garbage_collection.GarbageCollection(FakeConfig(printer))
        assert "klippy:ready" in printer.handlers
        assert "klippy:disconnect" in printer.handlers

        printer.handlers["klippy:ready"]()
        assert calls[:4] == [
            ("collect", 0), ("collect", 1), ("collect", 2), ("freeze", None)]
        printer.handlers["klippy:disconnect"]()
        assert calls[-1] == ("unfreeze", None)
    finally:
        for name, value in original.items():
            if value is missing:
                delattr(gc, name)
            else:
                setattr(gc, name, value)


def test_frozen_status_snapshot():
    source = {
        "printer": {"max_velocity": 500.0, "axes": ["x", "y", "z"]},
        "probe": {"samples": (1, 2, 3)},
    }
    frozen = configfile.freeze_status(source)

    assert isinstance(frozen, configfile.FrozenStatusDict)
    assert isinstance(frozen["printer"], configfile.FrozenStatusDict)
    assert frozen["printer"]["axes"] == ("x", "y", "z")
    assert copy.deepcopy(frozen) is frozen
    assert copy.deepcopy(frozen["printer"]) is frozen["printer"]

    try:
        frozen["printer"]["max_velocity"] = 300.0
        raise AssertionError("nested frozen status accepted mutation")
    except TypeError:
        pass

    try:
        frozen["new"] = 1
        raise AssertionError("frozen status accepted mutation")
    except TypeError:
        pass


def test_dynamic_status_is_still_copied():
    frozen = configfile.freeze_status({"printer": {"max_velocity": 500.0}})
    status = {
        "config": frozen,
        "warnings": [{"message": "test"}],
        "save_config_pending_items": {"probe": {"z_offset": "1.0"}},
    }
    snapshot = copy.deepcopy(status)

    assert snapshot["config"] is frozen
    assert snapshot["warnings"] is not status["warnings"]
    assert (snapshot["save_config_pending_items"]
            is not status["save_config_pending_items"])

    snapshot["warnings"][0]["message"] = "changed"
    snapshot["save_config_pending_items"]["probe"]["z_offset"] = "2.0"
    assert status["warnings"][0]["message"] == "test"
    assert status["save_config_pending_items"]["probe"]["z_offset"] == "1.0"


def main():
    test_garbage_collection_lifecycle()
    test_frozen_status_snapshot()
    test_dynamic_status_is_still_copied()
    print("GC optimization tests passed")


if __name__ == "__main__":
    main()
