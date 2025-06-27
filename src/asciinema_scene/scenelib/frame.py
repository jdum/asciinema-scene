from __future__ import annotations

import json
from math import floor
from typing import Any

from .constants import PRECISION, PRECISION_DECI


class Frame:
    __slots__ = ["timecode", "duration", "tpe", "text"]
    timecode: int
    duration: int
    tpe: str
    text: str

    def __init__(self) -> None:
        self.timecode = 0
        self.duration = 0
        self.tpe = ""
        self.text = ""

    def __str__(self) -> str:
        return self.dumps()

    @classmethod
    def parse(cls, frame_list: list[Any]) -> Frame:
        frame = cls()
        frame.timecode = int(round(frame_list[0] * PRECISION))
        frame.tpe = frame_list[1]
        frame.text = frame_list[2]
        return frame

    @property
    def tc_float(self) -> float:
        return round(self.timecode / PRECISION, PRECISION_DECI)  # type: ignore

    @property
    def tc_floor3(self) -> float:
        return floor(self.tc_float * 1000) / 1000

    @property
    def tc_floor6(self) -> float:
        return floor(self.tc_float * PRECISION) / PRECISION  # type: ignore

    @property
    def dur_float(self) -> float:
        return round(self.duration / PRECISION, PRECISION_DECI)  # type: ignore

    def as_list(self) -> list[Any]:
        return [self.tc_float, self.tpe, self.text]

    @property
    def timecode_duration_text_short_str(self) -> str:
        return f"{self.tc_floor3:7.3f}\u2502{self.dur_float:5.2f}\u2502 {self.text.strip()}\n"

    @property
    def timecode_duration_text_long_str(self) -> str:
        return f"{self.tc_floor6:10.6f}\u2502{self.dur_float:9.6f}\u2502 {self.text.strip()}\n"

    @property
    def timecode_duration_text_short_repr(self) -> str:
        return f"{self.tc_floor3:7.3f}\u2502{self.dur_float:5.2f}\u2502 {self.text!r}\n"

    @property
    def timecode_duration_text_long_repr(self) -> str:
        return (
            f"{self.tc_floor6:10.6f}\u2502{self.dur_float:9.6f}\u2502 {self.text!r}\n"
        )

    def set_duration(self, seconds: float) -> None:
        self.duration = int(round(seconds * PRECISION))

    def dumps(self) -> str:
        return json.dumps(
            self.as_list(),
            ensure_ascii=True,
            check_circular=False,
        )

    def copy(self) -> Frame:
        frame = Frame()
        frame.timecode = self.timecode
        frame.duration = self.duration
        frame.tpe = self.tpe
        frame.text = self.text
        return frame
