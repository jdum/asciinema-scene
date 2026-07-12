import json
from unittest.mock import patch

from click.testing import CliRunner

from asciinema_scene.sciine import cli

from .contents import SHORT_FILE_CONTENT, SHORT_V3_FILE_CONTENT

PATCH_TIMEOUT = "asciinema_scene.scenelib.scene_content.detect_stdin_timeout"


def test_convert_v2_to_v3():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(
            cli, ["convert", "--format", "v3"], input=SHORT_FILE_CONTENT
        )
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    header = json.loads(lines[0])
    assert header["version"] == 3
    assert "term" in header
    assert header["term"]["cols"] == 133
    # Events should have relative intervals
    event1 = json.loads(lines[1])
    assert event1[0] == 0.0  # first frame after t0 normalization


def test_convert_v3_to_v2():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(
            cli, ["convert", "--format", "v2"], input=SHORT_V3_FILE_CONTENT
        )
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    header = json.loads(lines[0])
    assert header["version"] == 2
    assert header["width"] == 133
    assert header["height"] == 36
    # Events should have absolute timecodes
    event1 = json.loads(lines[1])
    assert event1[0] == 0.0  # first frame (t0 normalized)


def test_convert_requires_format_option():
    runner = CliRunner()
    result = runner.invoke(cli, ["convert"], input=SHORT_FILE_CONTENT)
    assert result.exit_code != 0


def test_convert_v2_to_v3_maps_env_term_to_term_type():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(
            cli, ["convert", "--format", "v3"], input=SHORT_FILE_CONTENT
        )
    assert result.exit_code == 0
    header = json.loads(result.output.split("\n")[0])
    # short.cast has env.TERM = "linux"
    assert header["term"]["type"] == "linux"
    # TERM should not be in env (promoted to term.type)
    if "env" in header:
        assert "TERM" not in header["env"]


def test_convert_v3_to_v2_maps_term_type_to_env_term():
    runner = CliRunner()
    with patch(PATCH_TIMEOUT):
        result = runner.invoke(
            cli, ["convert", "--format", "v2"], input=SHORT_V3_FILE_CONTENT
        )
    assert result.exit_code == 0
    header = json.loads(result.output.split("\n")[0])
    assert header["env"]["TERM"] == "linux"
    assert "term" not in header
