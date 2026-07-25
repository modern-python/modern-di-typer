from typer.testing import CliRunner

from examples.app import app, container


def test_example_resolves_and_greets() -> None:
    runner = CliRunner()
    with container:
        result = runner.invoke(app, ["world"])
    assert result.exit_code == 0, result.output
    assert result.stdout == "Hello, world!\n"
