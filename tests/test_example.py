import runpy
import sys

import pytest
from typer.testing import CliRunner

from examples.app import app, container


def test_example_resolves_and_greets() -> None:
    runner = CliRunner()
    with container:
        result = runner.invoke(app, ["world"])
    assert result.exit_code == 0, result.output
    assert result.stdout == "Hello, world!\n"


def test_example_runs_as_a_script(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "argv", ["app", "world"])
    monkeypatch.delitem(sys.modules, "examples.app")
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("examples.app", run_name="__main__")
    assert exc_info.value.code == 0
    assert capsys.readouterr().out == "Hello, world!\n"
