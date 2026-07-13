import json
import tempfile
import time
from importlib import resources as rso
from pathlib import Path

import pytest

from asciinema_scene.scenelib.scene_content import SceneContent

from .contents import LONG_FILE_CONTENT, SHORT_FILE_CONTENT


def test_parse_status_short():
    scene = SceneContent()
    scene.parse_content(SHORT_FILE_CONTENT)
    expected = (
        "Input: string\nDate: 2023-05-28 11:15:06+00:00\nFrames: 22\nDuration: 6.135993"
    )
    result = scene.info
    assert result == expected


def test_parse_status_long():
    scene = SceneContent()
    scene.parse_content(LONG_FILE_CONTENT)
    expected = (
        "Input: string\nDate: 2023-05-28 11:11:21+00:00\n"
        "Frames: 71369\nDuration: 16.789319"
    )
    result = scene.info
    assert result == expected


def test_scene_header_short():
    scene = SceneContent()
    scene.parse_content(SHORT_FILE_CONTENT)
    expected = {
        "env": {"SHELL": "/bin/bash", "TERM": "linux"},
        "height": 36,
        "timestamp": 1685272506,
        "version": 2,
        "width": 133,
    }
    result = scene.header
    assert result == expected


def test_scene_header_short_2():
    scene = SceneContent()
    content = SHORT_FILE_CONTENT + '{"env": "duplicate header"}\n'
    scene.parse_content(content)
    expected = {
        "env": {"SHELL": "/bin/bash", "TERM": "linux"},
        "height": 36,
        "timestamp": 1685272506,
        "version": 2,
        "width": 133,
    }
    result = scene.header
    assert result == expected


def test_scene_header_long():
    scene = SceneContent()
    scene.parse_content(LONG_FILE_CONTENT)
    expected = {
        "env": {"SHELL": "/bin/bash", "TERM": "linux"},
        "height": 36,
        "timestamp": 1685272281,
        "version": 2,
        "width": 133,
    }
    result = scene.header
    assert result == expected


def test_scene_str():
    scene = SceneContent()
    scene.parse_content(SHORT_FILE_CONTENT)
    result = str(scene)
    assert result == (
        "<Scene 'string', 2023-05-28 11:15:06+00:00, Frames:22, Duration:6.136>"
    )


def test_raise_parse():
    scene = SceneContent()
    with pytest.raises(json.decoder.JSONDecodeError):
        scene.parse_content("wrong content!")


def test_raise_parse_2():
    with pytest.raises(FileNotFoundError):
        SceneContent.parse("test no existing file")


def test_parse_file_cast():
    for file in rso.files("tests.files").iterdir():
        if file.name == "short.cast":
            with rso.as_file(file) as actual_path:
                scene = SceneContent.parse(actual_path)
                result = str(scene)
                assert result == (
                    "<Scene 'short.cast', 2023-05-28 11:15:06+00:00, "
                    "Frames:22, Duration:6.136>"
                )
                break


def test_parse_file_gz():
    for file in rso.files("tests.files").iterdir():
        if file.name == "long.cast.gz":
            with rso.as_file(file) as actual_path:
                scene = SceneContent.parse(actual_path)
                result = str(scene)
                assert result == (
                    "<Scene 'long.cast.gz', 2023-05-28 11:11:21+00:00, "
                    "Frames:71369, Duration:16.789>"
                )
                break


def test_parse_file_zip():
    for file in rso.files("tests.files").iterdir():
        if file.name == "short.cast.zip":
            with rso.as_file(file) as actual_path:
                scene = SceneContent.parse(actual_path)
                result = str(scene)
                assert result == (
                    "<Scene 'short.cast.zip', 2023-05-28 11:15:06+00:00, "
                    "Frames:22, Duration:6.136>"
                )
                break


def test_duplicate():
    scene = SceneContent()
    scene.parse_content(SHORT_FILE_CONTENT)
    result = scene.duplicate()
    assert id(scene) != id(result)
    assert scene.header == result.header
    assert str(scene) == str(result)
    assert id(scene.frames[5]) != id(result.frames[5])
    assert str(scene.frames[5].as_list()) == str(result.frames[5].as_list())


def test_timestamp():
    scene = SceneContent()
    scene.parse_content(SHORT_FILE_CONTENT)
    result = scene.header["timestamp"]
    assert result == 1685272506


def test_set_timestamp():
    scene = SceneContent()
    scene.parse_content(SHORT_FILE_CONTENT)
    scene.set_timestamp()
    result = scene.header["timestamp"]
    assert time.time() - result < 3


def test_length():
    scene = SceneContent()
    scene.parse_content(SHORT_FILE_CONTENT)
    result = scene.length
    assert result == 22


def test_duration():
    scene = SceneContent()
    scene.parse_content(SHORT_FILE_CONTENT)
    result = scene.duration
    assert result == 6.135993


def test_dumps():
    scene = SceneContent()
    scene.parse_content(SHORT_FILE_CONTENT)
    dump = scene.dumps()
    scene2 = SceneContent()
    scene2.parse_content(dump)
    result = scene2.dumps()
    assert result == dump


def test_dump():
    scene = SceneContent()
    scene.parse_content(SHORT_FILE_CONTENT)
    with tempfile.TemporaryDirectory() as tmp_folder:
        cast_file = Path(tmp_folder) / "tmp.cast"
        scene.dump(cast_file)
        scene2 = SceneContent.parse(cast_file)
    expected = scene.dumps()
    result = scene2.dumps()
    assert result == expected


def test_set_format_version_int():
    scene = SceneContent()
    scene.set_format_version(3)
    assert scene.format_version == 3


def test_set_format_version_str():
    scene = SceneContent()
    scene.set_format_version("v3")
    assert scene.format_version == 3


def test_set_format_version_str_v2_builds_v2_header():
    scene = SceneContent()
    scene.header = {"version": 3, "term": {"type": "linux"}}
    scene.set_format_version("v2")
    assert scene.format_version == 2
    assert scene.header["version"] == 2
    assert scene.header["env"]["TERM"] == "linux"
    assert "term" not in scene.header


def test_set_format_version_unknown_string():
    scene = SceneContent()
    with pytest.raises(ValueError, match="Unknown version"):
        scene.set_format_version("foo")


def test_set_format_version_unknown_int():
    scene = SceneContent()
    with pytest.raises(ValueError, match="Unknown version"):
        scene.set_format_version(99)


def test_build_v3_header_no_env():
    scene = SceneContent()
    scene.header = {"version": 3, "width": 80, "height": 24}
    header = scene._build_v3_header()
    assert "env" not in header


def test_build_v3_header_env_term_only():
    scene = SceneContent()
    scene.header = {"version": 3, "width": 80, "height": 24, "env": {"TERM": "linux"}}
    header = scene._build_v3_header()
    assert "env" not in header


def test_build_v3_header_env_without_term():
    scene = SceneContent()
    scene.header = {
        "version": 3,
        "width": 80,
        "height": 24,
        "env": {"SHELL": "/bin/bash"},
    }
    header = scene._build_v3_header()
    assert header["env"] == {"SHELL": "/bin/bash"}


def test_build_v3_term_from_env_term():
    scene = SceneContent()
    scene.header = {
        "width": 80,
        "height": 24,
        "term": "xterm-256color",
        "env": {"TERM": "linux"},
    }
    term = scene._build_v3_term()
    assert term["type"] == "linux"


def test_build_v3_term_theme_from_header():
    scene = SceneContent()
    scene.header = {"width": 80, "height": 24, "term": {}, "theme": "dark"}
    term = scene._build_v3_term()
    assert term["theme"] == "dark"


def test_build_v2_header_from_term_dict():
    scene = SceneContent()
    scene.header = {
        "version": 3,
        "term": {"type": "linux", "theme": "dark"},
        "env": {"SHELL": "/bin/bash"},
    }
    scene._build_v2_header()
    assert scene.header["env"]["TERM"] == "linux"
    assert scene.header["theme"] == "dark"
    assert "term" not in scene.header


def test_build_v2_header_with_string_term():
    scene = SceneContent()
    scene.header = {
        "version": 3,
        "term": "xterm",
        "env": {"SHELL": "/bin/bash"},
    }
    scene._build_v2_header()
    assert "term" not in scene.header
    assert "TERM" not in scene.header.get("env", {})


def test_build_v2_header_term_dict_theme_only():
    scene = SceneContent()
    scene.header = {
        "version": 3,
        "term": {"theme": "dark"},
        "env": {"SHELL": "/bin/bash"},
    }
    scene._build_v2_header()
    assert scene.header["theme"] == "dark"
    assert "TERM" not in scene.header.get("env", {})
    assert "term" not in scene.header
