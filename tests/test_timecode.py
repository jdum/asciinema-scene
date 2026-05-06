import pytest
from click.exceptions import BadParameter

from asciinema_scene.sciine import TimecodeParamType

TIMECODE = TimecodeParamType()


def convert(value: str) -> float:
    return TIMECODE.convert(value, param=None, ctx=None)


def test_plain_integer():
    assert convert("90") == 90.0


def test_plain_float():
    assert convert("90.5") == 90.5


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


def test_negative_plain_seconds_accepted():
    # plain negative seconds: no range check, converts normally
    assert convert("-5") == -5.0


def test_negative_hours_rejected():
    with pytest.raises(BadParameter):
        convert("-1:0:0")


def test_float_minutes_accepted():
    # 1.5:30 = 90 + 30 = 120.0 — deliberate, document with test
    assert convert("1.5:30") == 120.0
