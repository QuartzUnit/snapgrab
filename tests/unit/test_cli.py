"""Tests for CLI."""

from click.testing import CliRunner

from snapgrab import __version__
from snapgrab.__main__ import main


runner = CliRunner()


def test_cli_version():
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_cli_no_args_shows_help():
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert "Snapgrab" in result.output or "Usage" in result.output


def test_cli_help():
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "url" in result.output.lower() or "meta" in result.output.lower()


def test_cli_url_help():
    result = runner.invoke(main, ["url", "--help"])
    assert result.exit_code == 0
    assert "--viewport" in result.output
    assert "--full-page" in result.output
    assert "--format" in result.output
    assert "--dark-mode" in result.output


def test_cli_meta_help():
    result = runner.invoke(main, ["meta", "--help"])
    assert result.exit_code == 0
    assert "metadata" in result.output.lower() or "URL" in result.output
