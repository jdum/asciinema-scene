from __future__ import annotations

import gzip
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from time import time
from typing import Any
from zipfile import ZipFile

from .frame import Frame
from .utils import detect_stdin_timeout


class SceneContent:
    def __init__(self) -> None:
        self.input_file: str = "string"
        self.header: dict[str, Any] = {}
        self.frames: list[Frame] = []

    @staticmethod
    def _decode(line: str) -> Any:
        try:
            return json.loads(line)
        except json.decoder.JSONDecodeError:
            print("---- Error ---------------------")
            print(line)
            print("--------------------------------")
            raise

    def __str__(self) -> str:
        return (
            f"<Scene {self.input_file!r}, {self.date}, "
            f"Frames:{self.length}, Duration:{self.duration:.3f}>"
        )

    def parse_content(self, raw_content: str) -> None:
        for line in raw_content.split("\n"):
            if not line:
                continue
            frame = self._decode(line)
            if isinstance(frame, list):
                self.frames.append(Frame.parse(frame))
                continue
            if not self.header and isinstance(frame, dict):
                self.header = frame
        self.pre_normalize()

    @classmethod
    def from_file(cls, input_file: str | Path) -> SceneContent:
        scene = SceneContent()
        path = Path(input_file)
        scene.input_file = path.name
        if path.suffix == ".gz":
            scene.parse_content(gzip.decompress(path.read_bytes()).decode("utf8"))
        elif path.suffix == ".zip":
            name = path.name[:-4]
            zf = ZipFile(path, "r")
            scene.parse_content(zf.read(name).decode("utf8"))
        else:
            scene.parse_content(path.read_text(encoding="utf8"))
        return scene

    @classmethod
    def parse(cls, input_file: str | Path | None = None) -> SceneContent:
        if input_file:
            return cls.from_file(input_file)
        detect_stdin_timeout()
        scene = SceneContent()
        scene.input_file = "sys.stdin"
        scene.parse_content("\n".join(list(sys.stdin)))
        return scene

    def duplicate(self) -> SceneContent:
        duplicate = SceneContent()
        duplicate.header = deepcopy(self.header)
        duplicate.frames = [line.copy() for line in self.frames]
        return duplicate

    def set_timestamp(self) -> None:
        self.header["timestamp"] = int(time())

    @property
    def info(self) -> str:
        return "\n".join(
            (
                f"Input: {self.input_file}",
                f"Date: {self.date}",
                f"Frames: {self.length}",
                f"Duration: {self.duration:.6f}",
            )
        )

    @property
    def date(self) -> str:
        timestamp = self.header.get("timestamp", 0)
        return datetime.fromtimestamp(timestamp, timezone.utc).isoformat(  # noqa: UP017
            " "
        )

    @property
    def length(self) -> int:
        return len(self.frames)

    @property
    def duration(self) -> float:
        if self.frames:
            last = self.frames[-1]
            return last.tc_float
        else:
            return 0.0

    def dumps(self) -> str:
        content = []
        content.append(
            json.dumps(
                self.header,
                ensure_ascii=True,
                check_circular=False,
            )
        )
        content.extend(frame.dumps() for frame in self.frames)
        content.append("")
        return "\n".join(content)

    def dump(self, output_file: str | Path | None = None) -> None:
        if output_file:
            Path(output_file).write_text(self.dumps(), encoding="utf8")
        else:
            sys.stdout.write(self.dumps())
            sys.stdout.flush()

    def _normalize_t0(self) -> None:
        if not self.frames:
            return
        first = self.frames[0]
        tc0 = first.timecode
        if tc0 == 0:
            return
        for frame in self.frames:
            frame.timecode -= tc0

    def _normalize_crlf(self) -> None:
        if not self.frames:
            return
        last = self.frames[-1]
        if not last.text.endswith("\r\n"):
            self.frames.append(
                Frame.parse([last.tc_float + last.dur_float, "o", "\r\n"])
            )

    def pre_normalize(self) -> None:
        self._normalize_crlf()
        self._normalize_t0()
        self.set_durations()

    def post_normalize(self) -> None:
        self._normalize_crlf()
        self._normalize_t0()
        self.set_durations()
        self.set_timestamp()

    def set_durations(self) -> None:
        if not self.frames:
            return
        last = self.frames[-1]
        last.duration = 0  # default for last message (0 millisec)
        next_tc = last.timecode
        for frame in reversed(self.frames[:-1]):
            frame.duration, next_tc = next_tc - frame.timecode, frame.timecode
