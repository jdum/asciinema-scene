from asciinema_scene.scenelib import SceneContent

from .contents import SHORT_FILE_CONTENT, SHORT_V3_FILE_CONTENT


def test_v3_parse_detects_version():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    assert scene.format_version == 3


def test_v3_parse_header_extracts_dimensions():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    assert scene.header["width"] == 133
    assert scene.header["height"] == 36


def test_v3_parse_converts_intervals_to_absolute_timecodes():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    assert scene.frames[0].tc_float == 0.0
    assert abs(scene.frames[1].tc_float - 0.894) < 0.001


def test_v3_parse_frame_count_matches_v2():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    assert scene.length == 22


def test_v3_parse_skips_comment_lines():
    content = '{"version": 3, "term": {"cols": 80, "rows": 24}}\n# this is a comment\n[0.5, "o", "hi"]\n'
    scene = SceneContent()
    scene.parse_content(content)
    assert scene.format_version == 3
    assert scene.length == 2


def test_v2_parse_still_works():
    """Regression: v2 parsing must still work after changes."""
    scene = SceneContent()
    scene.parse_content(SHORT_FILE_CONTENT)
    assert scene.format_version == 2
    assert scene.frames[0].tc_float == 0.0
    assert abs(scene.frames[1].tc_float - 0.894038) < 0.001
