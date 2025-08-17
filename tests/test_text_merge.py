from asciinema_scene.scenelib.scene import Scene

from .contents import BACK_FILE_CONTENT


def test_text_merge_0():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    scene.text_merge_frames("nothing")
    assert scene.length == 25


def test_text_merge():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    orig_duration = scene.duration
    scene.text_replace_frames(". {server}", "box")
    scene.text_merge_frames("box")
    assert scene.length == 2
    assert scene.duration == orig_duration


def test_text_merge_m1s():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    orig_duration = scene.duration
    scene.text_replace_frames(". {server}", "box")
    scene.text_merge_frames("box", start=1)
    assert scene.length == 7
    assert scene.duration == orig_duration


def test_text_merge_end_1s():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    orig_duration = scene.duration
    scene.text_replace_frames(". {server}", "box")
    scene.text_merge_frames("box", end=1)
    assert scene.length == 21
    assert scene.duration == orig_duration


def test_text_merge_m_start60():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    orig_duration = scene.duration
    scene.text_replace_frames(". {server}", "box")
    scene.text_merge_frames("box", start=60)
    assert scene.length == 25
    assert scene.duration == orig_duration


def test_text_merge_1s():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    orig_duration = scene.duration
    scene.text_replace_frames(". {server}", "box", start=1)
    scene.text_merge_frames("box")
    assert scene.length == 7
    assert scene.duration == orig_duration


def test_text_merge_e1s():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    orig_duration = scene.duration
    scene.text_replace_frames(". {server}", "box", end=1)
    scene.text_merge_frames("box")
    assert scene.length == 21
    assert scene.duration == orig_duration


def test_text_merge_1s_o():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    orig_duration = scene.duration
    scene.frames[10].tpe = "i"
    scene.text_replace_frames(". {server}", "box", start=1)
    scene.text_merge_frames("box")
    assert scene.length == 9
    assert scene.duration == orig_duration


def test_text_merge_60s():
    scene = Scene()
    scene.parse_content(BACK_FILE_CONTENT)
    orig_duration = scene.duration
    scene.text_replace_frames(". {server}", "box", start=60)
    scene.text_merge_frames("box")
    assert scene.length == 25
    assert scene.duration == orig_duration
