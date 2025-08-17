from asciinema_scene.scenelib.scene import Scene

from .contents import BACK_FILE_CONTENT


def test_text_replace():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    scene.text_replace_frames(". {server}", "box")
    assert scene.frames[1].text.endswith("  box\r")
    assert scene.frames[10].text.endswith("  box\r")
    assert scene.frames[23].text.endswith("  box\r")


def test_text_replace_1s():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    scene.text_replace_frames(". {server}", "box", start=1)
    assert scene.frames[1].text.endswith(" {server}\r")
    assert scene.frames[10].text.endswith("  box\r")
    assert scene.frames[23].text.endswith("  box\r")


def test_text_replace_e1s():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    scene.text_replace_frames(". {server}", "box", end=1)
    assert scene.frames[1].text.endswith("  box\r")
    assert scene.frames[10].text.endswith(" {server}\r")
    assert scene.frames[23].text.endswith(" {server}\r")


def test_text_replace_1s_o():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    scene.frames[10].tpe = "i"
    scene.text_replace_frames(". {server}", "box", start=1)
    assert scene.frames[1].text.endswith(" {server}\r")
    assert scene.frames[10].text.endswith(" {server}\r")
    assert scene.frames[23].text.endswith("  box\r")


def test_text_replace_60s():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    scene.text_replace_frames(". {server}", "box", start=60)
    assert scene.frames[1].text.endswith(" {server}\r")
    assert scene.frames[10].text.endswith(" {server}\r")
    assert scene.frames[23].text.endswith(" {server}\r")
