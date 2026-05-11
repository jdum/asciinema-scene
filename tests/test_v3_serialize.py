import json

from asciinema_scene.scenelib import SceneContent

from .contents import SHORT_FILE_CONTENT, SHORT_V3_FILE_CONTENT


def test_v3_dumps_produces_v3_header() -> None:
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    output = scene.dumps()
    header = json.loads(output.split("\n")[0])
    assert header["version"] == 3
    assert "term" in header
    assert header["term"]["cols"] == 133
    assert header["term"]["rows"] == 36


def test_v3_dumps_uses_relative_intervals() -> None:
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    output = scene.dumps()
    lines = output.strip().split("\n")
    # First event line - after t0 normalization, first timecode is 0
    event1 = json.loads(lines[1])
    assert event1[0] == 0.0
    # Second event: should be interval from first to second
    event2 = json.loads(lines[2])
    assert event2[0] > 0


def test_v3_round_trip_preserves_content() -> None:
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    output = scene.dumps()
    # Re-parse the output
    scene2 = SceneContent()
    scene2.parse_content(output)
    assert scene2.format_version == 3
    assert scene2.length == scene.length
    # Timecodes should match within microsecond precision
    for f1, f2 in zip(scene.frames, scene2.frames):
        assert abs(f1.timecode - f2.timecode) <= 1
        assert f1.tpe == f2.tpe
        assert f1.text == f2.text


def test_v3_header_no_width_height_top_level() -> None:
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    output = scene.dumps()
    header = json.loads(output.split("\n")[0])
    assert "width" not in header
    assert "height" not in header


def test_v3_header_preserves_env() -> None:
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    output = scene.dumps()
    header = json.loads(output.split("\n")[0])
    assert header["env"] == {"SHELL": "/bin/bash"}


def test_v3_header_has_term_type() -> None:
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    output = scene.dumps()
    header = json.loads(output.split("\n")[0])
    assert header["term"]["type"] == "linux"


def test_v2_dumps_still_works() -> None:
    """Regression: v2 serialization unchanged."""
    scene = SceneContent()
    scene.parse_content(SHORT_FILE_CONTENT)
    output = scene.dumps()
    header = json.loads(output.split("\n")[0])
    assert header["version"] == 2
    assert header["width"] == 133
    assert "term" not in header
