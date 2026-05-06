"""Integration tests: all existing commands work correctly with v3 input."""

import json
from unittest.mock import patch

from click.testing import CliRunner

from asciinema_scene.sciine import cli
from .contents import SHORT_V3_FILE_CONTENT

PATCH_TIMEOUT = "asciinema_scene.scenelib.scene_content.detect_stdin_timeout"


def _get_header(output: str) -> dict:
    return json.loads(output.split("\n")[0])


def _get_events(output: str) -> list:
    lines = output.strip().split("\n")
    return [json.loads(line) for line in lines[1:] if line]


def test_status_with_v3():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(cli, ["status"], input=SHORT_V3_FILE_CONTENT)
    assert result.exit_code == 0
    assert "Frames:" in result.output
    assert "Duration:" in result.output


def test_header_with_v3():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(cli, ["header"], input=SHORT_V3_FILE_CONTENT)
    assert result.exit_code == 0
    assert "width" in result.output or "cols" in result.output


def test_show_with_v3():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(
            cli, ["show", "--lines", "5"], input=SHORT_V3_FILE_CONTENT
        )
    assert result.exit_code == 0
    # Should show timecode/duration/text lines
    assert "\u2502" in result.output  # pipe separator used in show


def test_cut_with_v3():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(
            cli, ["cut", "--start", "1.0", "--end", "3.0"],
            input=SHORT_V3_FILE_CONTENT,
        )
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3


def test_copy_with_v3():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(
            cli, ["copy", "--start", "1.0", "--end", "3.0"],
            input=SHORT_V3_FILE_CONTENT,
        )
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3


def test_speed_with_v3():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(cli, ["speed", "2.0"], input=SHORT_V3_FILE_CONTENT)
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3


def test_maximum_with_v3():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(cli, ["maximum", "0.5"], input=SHORT_V3_FILE_CONTENT)
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3


def test_minimum_with_v3():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(cli, ["minimum", "0.1"], input=SHORT_V3_FILE_CONTENT)
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3


def test_quantize_with_v3():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(
            cli, ["quantize", "0.1", "0.5", "0.2"], input=SHORT_V3_FILE_CONTENT
        )
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3


def test_text_delete_with_v3():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(
            cli, ["text-delete", "short"], input=SHORT_V3_FILE_CONTENT
        )
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3


def test_text_replace_with_v3():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(
            cli, ["text-replace", "short", "long"], input=SHORT_V3_FILE_CONTENT
        )
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3
