from unittest.mock import patch

import pytest
from click.exceptions import BadParameter
from click.testing import CliRunner, Result

from asciinema_scene.sciine import TimecodeParamType, cli

from .contents import SHORT_FILE_CONTENT

TIMECODE = TimecodeParamType()


def convert(value: str) -> float:
    return TIMECODE.convert(value, param=None, ctx=None)


def test_plain_integer():
    assert convert("90") == 90.0


def test_plain_float():
    assert convert("90.5") == 90.5


def test_convert_int():
    assert convert(90) == 90.0


def test_convert_float():
    assert convert(90.5) == 90.5


def test_minutes_seconds():
    assert convert("1:30") == 90.0


def test_minutes_seconds_decimal():
    assert convert("1:30.5") == 90.5


def test_hours_minutes_seconds():
    assert convert("1:30:25") == 5425.0


def test_hours_minutes_seconds_decimal():
    assert convert("1:30:25.5") == 5425.5


def test_zero_ms():
    assert convert("0:0") == 0.0


def test_zero_hms():
    assert convert("0:0:0") == 0.0


def test_seconds_out_of_range():
    with pytest.raises(BadParameter):
        convert("1:60")


def test_minutes_out_of_range():
    with pytest.raises(BadParameter):
        convert("1:60:00")


def test_non_numeric():
    with pytest.raises(BadParameter):
        convert("abc")


def test_too_many_parts():
    with pytest.raises(BadParameter):
        convert("1:2:3:4")


def test_negative_rejected():
    with pytest.raises(BadParameter):
        convert("1:-1")


def test_negative_minutes_rejected():
    with pytest.raises(BadParameter):
        convert("-1:30")


def test_negative_plain_seconds_accepted():
    # plain negative seconds: no range check, converts normally
    assert convert("-5") == -5.0


def test_negative_hours_rejected():
    with pytest.raises(BadParameter):
        convert("-1:0:0")


def test_float_minutes_accepted():
    # 1.5:30 = 90 + 30 = 120.0 — deliberate, document with test
    assert convert("1.5:30") == 120.0


def _invoke_cut(args: list[str]) -> Result:
    runner = CliRunner()
    with patch("asciinema_scene.scenelib.scene_content.detect_stdin_timeout"):
        return runner.invoke(cli, ["cut", *args], input=SHORT_FILE_CONTENT)


def test_cut_with_colon_start():
    result = _invoke_cut(["--start", "0:04"])
    assert result.exit_code == 0


def test_cut_with_colon_start_end():
    result = _invoke_cut(["--start", "0:04", "--end", "0:10"])
    assert result.exit_code == 0


def test_cut_with_hms():
    result = _invoke_cut(["--start", "0:0:4", "--end", "0:0:10"])
    assert result.exit_code == 0


def test_invalid_timecode_error():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["cut", "--start", "bad"],
        input=SHORT_FILE_CONTENT,
    )
    assert result.exit_code != 0
    assert "timecode" in result.output.lower() or "invalid" in result.output.lower()
