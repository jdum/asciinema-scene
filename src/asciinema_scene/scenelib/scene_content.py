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

from .constants import PRECISION
from .frame import Frame
from .utils import detect_stdin_timeout


class SceneContent:
    def __init__(self) -> None:
        self.input_file: str = "string"
        self.header: dict[str, Any] = {}
        self.frames: list[Frame] = []
        self.format_version: int = 2

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
            if not line or line.startswith("#"):
                continue
            frame = self._decode(line)
            if isinstance(frame, list):
                self.frames.append(Frame.parse(frame))
                continue
            if not self.header and isinstance(frame, dict):
                self.header = frame
        self.format_version = self.header.get("version", 2)
        if self.format_version == 3:
            self._convert_v3()
        self.pre_normalize()

    def _convert_v3(self) -> None:
        """Convert v3 format: extract dimensions and convert intervals to absolute timecodes."""
        term = self.header.get("term", {})
        self.header["width"] = term.get("cols", 80)
        self.header["height"] = term.get("rows", 24)
        # Convert relative intervals to absolute timecodes
        cumulative = 0
        for frame in self.frames:
            cumulative += frame.timecode
            frame.timecode = cumulative

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
        if self.format_version == 3:
            return self._dumps_v3()
        return self._dumps_v2()

    def _dumps_v2(self) -> str:
        content = []
        header = {k: v for k, v in self.header.items() if not k.startswith("_")}
        content.append(
            json.dumps(
                header,
                ensure_ascii=True,
                check_circular=False,
            )
        )
        content.extend(frame.dumps() for frame in self.frames)
        content.append("")
        return "\n".join(content)

    def _dumps_v3(self) -> str:
        content = []
        header = self._build_v3_header()
        content.append(
            json.dumps(
                header,
                ensure_ascii=True,
                check_circular=False,
            )
        )
        # Convert absolute timecodes to relative intervals
        prev_tc = 0
        for frame in self.frames:
            interval = (frame.timecode - prev_tc) / PRECISION
            # Round to 3 decimal places (millisecond precision)
            interval_rounded = round(interval, 3)
            event = [interval_rounded, frame.tpe, frame.text]
            content.append(
                json.dumps(event, ensure_ascii=True, check_circular=False)
            )
            prev_tc = frame.timecode
        content.append("")
        return "\n".join(content)

    def _build_v3_header(self) -> dict[str, Any]:
        """Build v3 header from internal representation."""
        term = self._build_v3_term()
        header: dict[str, Any] = {"version": 3, "term": term}
        for key in ("timestamp", "idle_time_limit", "command", "title", "tags"):
            if key in self.header:
                header[key] = self.header[key]
        # Copy env without TERM (promoted to term.type)
        if "env" in self.header:
            env = {k: v for k, v in self.header["env"].items() if k != "TERM"}
            if env:
                header["env"] = env
        return header

    def _build_v3_term(self) -> dict[str, Any]:
        """Build v3 term dict from internal header."""
        term: dict[str, Any] = {
            "cols": self.header.get("width", 80),
            "rows": self.header.get("height", 24),
        }
        orig_term = self.header.get("term", {})
        if isinstance(orig_term, dict):
            for key in ("type", "version", "theme"):
                if key in orig_term:
                    term[key] = orig_term[key]
        if "type" not in term and "env" in self.header:
            env = self.header.get("env", {})
            if "TERM" in env:
                term["type"] = env["TERM"]
        if "theme" not in term and "theme" in self.header:
            term["theme"] = self.header["theme"]
        return term

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
        next_tc = last.timecode
        for frame in reversed(self.frames[:-1]):
            frame.duration, next_tc = next_tc - frame.timecode, frame.timecode
