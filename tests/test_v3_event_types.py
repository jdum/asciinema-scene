import json

from asciinema_scene.scenelib import SceneContent


V3_WITH_ALL_EVENTS = """\
{"version": 3, "term": {"cols": 80, "rows": 24}}
[0.5, "o", "hello"]
[1.0, "m", "chapter1"]
[0.5, "o", " world"]
[2.0, "r", "100x50"]
[1.0, "o", "bye"]
[0.5, "x", "0"]
"""


def test_parse_marker_event():
    scene = SceneContent()
    scene.parse_content(V3_WITH_ALL_EVENTS)
    markers = [f for f in scene.frames if f.tpe == "m"]
    assert len(markers) == 1
    assert markers[0].text == "chapter1"


def test_parse_resize_event():
    scene = SceneContent()
    scene.parse_content(V3_WITH_ALL_EVENTS)
    resizes = [f for f in scene.frames if f.tpe == "r"]
    assert len(resizes) == 1
    assert resizes[0].text == "100x50"


def test_parse_exit_event():
    scene = SceneContent()
    scene.parse_content(V3_WITH_ALL_EVENTS)
    exits = [f for f in scene.frames if f.tpe == "x"]
    assert len(exits) == 1
    assert exits[0].text == "0"


def test_round_trip_preserves_all_event_types():
    scene = SceneContent()
    scene.parse_content(V3_WITH_ALL_EVENTS)
    output = scene.dumps()
    scene2 = SceneContent()
    scene2.parse_content(output)
    types_original = [f.tpe for f in scene.frames]
    types_roundtrip = [f.tpe for f in scene2.frames]
    assert types_original == types_roundtrip


def test_serialize_all_event_types_as_v3():
    scene = SceneContent()
    scene.parse_content(V3_WITH_ALL_EVENTS)
    output = scene.dumps()
    lines = output.strip().split("\n")
    events = [json.loads(line) for line in lines[1:]]
    types = [e[1] for e in events]
    assert "m" in types
    assert "r" in types
    assert "x" in types
    assert "o" in types
