from asciinema_scene.scenelib.scene import Scene

from .contents import SHORT_FILE_CONTENT


def some_scene() -> Scene:
    scene = Scene()
    scene.parse_content(
        """{"version": 2, "width": 133, "height": 36, "timestamp": 1685272506, "env": {"SHELL": "/bin/bash", "TERM": "linux"}}
[0.0, "o", "aaa"]
[0.1, "o", "bbb"]
[0.2, "o", "ccc"]
[0.3, "o", "ddd"]
"""
    )
    return scene


def test_include_0():
    scene = Scene()
    scene.parse_content(SHORT_FILE_CONTENT)
    inc_scene = some_scene()
    scene.include_scene(0.0, inc_scene)
    assert scene.length == 27
    assert scene.duration == 6.435993


def test_insert_1():
    scene = Scene()
    scene.parse_content(SHORT_FILE_CONTENT)
    inc_scene = some_scene()
    scene.include_scene(2.0, inc_scene)
    assert scene.length == 27
    assert scene.duration == 6.435993


def test_insert_last():
    scene = Scene()
    scene.parse_content(SHORT_FILE_CONTENT)
    inc_scene = some_scene()
    scene.include_scene(999.0, inc_scene)
    assert scene.length == 27
    assert scene.duration == 6.435993


def test_insert_last_empty():
    scene = Scene()
    inc_scene = some_scene()
    print(scene)
    scene.include_scene(10000.0, inc_scene)
    assert scene.length == 5
    assert scene.duration == 0.3
