import os
import pytest
from tests.helpers.cli_loader import load_script


def test_is_runnable_subcommand_requires_executable_file(tmp_path, monkeypatch):
    cli = load_script("multivision")
    sub = tmp_path / "multivision-demo"
    sub.write_text("#!/bin/sh\n")

    monkeypatch.setattr(os, "access", lambda p, mode: False)
    assert cli._is_runnable_subcommand(sub) is False

    monkeypatch.setattr(os, "access", lambda p, mode: True)
    assert cli._is_runnable_subcommand(sub) is True
