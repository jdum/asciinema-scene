from __future__ import annotations

from dataclasses import dataclass

import pyte

from .constants import PRECISION
from .frame import Frame


@dataclass
class CollapseRegion:
    """A detected region of repetitive frames."""

    start_idx: int
    end_idx: int
    duration: float  # in seconds


def _screen_snapshot(screen: pyte.Screen) -> str:
    """Capture the current screen buffer as a flat string."""
    return "".join(
        screen.buffer[row][col].data
        for row in range(screen.lines)
        for col in range(screen.columns)
    )


def _change_ratio(prev: str, current: str) -> float:
    """Compute the ratio of changed cells between two snapshots."""
    if not prev:
        return 1.0
    total = len(prev)
    if total == 0:
        return 0.0
    changed = sum(1 for a, b in zip(prev, current, strict=False) if a != b)
    return changed / total


def _build_screen(
    frames: list[Frame],
    cols: int,
    rows: int,
    up_to: int,
) -> tuple[pyte.Screen, pyte.Stream]:
    """Create a pyte screen fed with frames up to the given index."""
    screen = pyte.Screen(cols, rows)
    stream = pyte.Stream(screen)
    for frame in frames[:up_to]:
        if frame.tpe == "o":
            stream.feed(frame.text)
    return screen, stream


def _process_frame(
    frame: Frame,
    stream: pyte.Stream,
    screen: pyte.Screen,
    prev_snapshot: str,
    threshold: float,
) -> tuple[str, bool]:
    """Feed a frame and return (new_snapshot, is_similar)."""
    if frame.tpe == "o":
        stream.feed(frame.text)
    current = _screen_snapshot(screen)
    ratio = _change_ratio(prev_snapshot, current)
    return current, ratio <= threshold


def detect_collapse_regions(
    frames: list[Frame],
    cols: int,
    rows: int,
    start_idx: int = 0,
    end_idx: int | None = None,
    threshold: float = 0.05,
    min_duration: float = 2.0,
) -> list[CollapseRegion]:
    """Detect repetitive regions using pyte screen comparison."""
    if end_idx is None:
        end_idx = len(frames)
    if end_idx <= start_idx or not frames:
        return []

    screen, stream = _build_screen(frames, cols, rows, start_idx)

    # Feed the first frame as the baseline
    first_frame = frames[start_idx]
    if first_frame.tpe == "o":
        stream.feed(first_frame.text)
    prev_snapshot = _screen_snapshot(screen)

    run_start: int | None = None
    regions: list[CollapseRegion] = []

    for idx in range(start_idx + 1, end_idx):
        current_snapshot, is_similar = _process_frame(
            frames[idx], stream, screen, prev_snapshot, threshold,
        )

        if is_similar:
            if run_start is None:
                run_start = idx
        elif run_start is not None:
            _maybe_add_region(regions, frames, run_start, idx, min_duration)
            run_start = None

        prev_snapshot = current_snapshot

    # Close any open run at the end
    if run_start is not None:
        _maybe_add_region(regions, frames, run_start, end_idx, min_duration)

    return regions


def _maybe_add_region(
    regions: list[CollapseRegion],
    frames: list[Frame],
    start_idx: int,
    end_idx: int,
    min_duration: float,
) -> None:
    """Add a region if its duration meets the minimum threshold."""
    first = frames[start_idx]
    last = frames[end_idx - 1]
    duration = (last.timecode + last.duration - first.timecode) / PRECISION
    if duration >= min_duration:
        regions.append(
            CollapseRegion(
                start_idx=start_idx,
                end_idx=end_idx,
                duration=duration,
            ),
        )
