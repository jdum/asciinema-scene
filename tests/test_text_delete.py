
from asciinema_scene.scenelib.scene import Scene

from .contents import BACK_FILE_CONTENT


def test_back_file_status():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    assert scene.duration - 5 < 0.2
    assert scene.length == 25


def test_text_delete():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    scene.text_delete_frames("{server}")
    assert scene.length == 1


def test_text_delete_1s():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    scene.text_delete_frames("{server}", start=1)
    assert scene.length == 6


def test_text_delete_1s_o():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    scene.frames[10].tpe = "i"
    scene.text_delete_frames("{server}", start=1)
    assert scene.length == 7


def test_text_delete_60s():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    scene.text_delete_frames("{server}", start=60)
    assert scene.length == 25
