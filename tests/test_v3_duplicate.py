import json

from asciinema_scene.scenelib import SceneContent

from .contents import SHORT_V3_FILE_CONTENT


def test_duplicate_preserves_format_version():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    dup = scene.duplicate()
    assert dup.format_version == 3


def test_duplicate_v3_produces_v3_output():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    dup = scene.duplicate()
    output = dup.dumps()
    header = json.loads(output.split("\n")[0])
    assert header["version"] == 3
