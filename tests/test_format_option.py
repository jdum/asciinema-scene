import json
from unittest.mock import patch

from click.testing import CliRunner

from asciinema_scene.sciine import cli
from .contents import SHORT_FILE_CONTENT, SHORT_V3_FILE_CONTENT

PATCH_TIMEOUT = "asciinema_scene.scenelib.scene_content.detect_stdin_timeout"


def test_cut_preserves_v3_format():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(
            cli, ["cut", "--start", "1.0", "--end", "2.0"], input=SHORT_V3_FILE_CONTENT
        )
    assert result.exit_code == 0
    header = json.loads(result.output.split("\n")[0])
    assert header["version"] == 3


def test_cut_with_format_v3_converts_v2_input():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(
            cli, ["cut", "--start", "1.0", "--end", "2.0", "--format", "v3"],
            input=SHORT_FILE_CONTENT,
        )
    assert result.exit_code == 0
    header = json.loads(result.output.split("\n")[0])
    assert header["version"] == 3


def test_speed_preserves_v2_format():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(
            cli, ["speed", "2.0"], input=SHORT_FILE_CONTENT
        )
    assert result.exit_code == 0
    header = json.loads(result.output.split("\n")[0])
    assert header["version"] == 2


def test_speed_with_format_v2_from_v3_input():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(
            cli, ["speed", "2.0", "--format", "v2"], input=SHORT_V3_FILE_CONTENT
        )
    assert result.exit_code == 0
    header = json.loads(result.output.split("\n")[0])
    assert header["version"] == 2
