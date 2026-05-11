# Collapse Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `collapse` command that detects repetitive terminal regions (spinners, progress bars) using pyte screen emulation and speeds them up to a target duration.

**Architecture:** New `collapse.py` module in `scenelib/` handles detection via pyte virtual terminal. `Scene.collapse()` orchestrates detection and speed adjustment. CLI command follows existing patterns.

**Tech Stack:** Python, pyte (terminal emulator), Click (CLI)

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `pyproject.toml` | Modify | Add `pyte` dependency |
| `src/asciinema_scene/scenelib/collapse.py` | Create | Region detection logic using pyte |
| `src/asciinema_scene/scenelib/scene.py` | Modify | Add `collapse()` method |
| `src/asciinema_scene/sciine.py` | Modify | Add `collapse` CLI command |
| `tests/test_collapse.py` | Create | Tests for collapse feature |

---

### Task 1: Add pyte dependency

**Files:**
- Modify: `pyproject.toml:19-21`

- [ ] **Step 1: Add pyte to project dependencies**

In `pyproject.toml`, add `pyte` to the `dependencies` list:

```toml
dependencies = [
    "click>=8.3.0,<9",
    "pyte>=0.8.0,<1",
]
```

- [ ] **Step 2: Sync dependencies**

Run: `uv sync`
Expected: pyte installs successfully

- [ ] **Step 3: Verify pyte imports**

Run: `uv run python -c "import pyte; print(pyte.__version__)"`
Expected: Prints version number (0.8.x)

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add pyte dependency for collapse command"
```

---

### Task 2: Create collapse detection module with tests

**Files:**
- Create: `src/asciinema_scene/scenelib/collapse.py`
- Create: `tests/test_collapse.py`

- [ ] **Step 1: Write failing tests for `detect_collapse_regions`**

Create `tests/test_collapse.py`:

```python
from asciinema_scene.scenelib.collapse import CollapseRegion, detect_collapse_regions
from asciinema_scene.scenelib.frame import Frame
from asciinema_scene.scenelib.constants import PRECISION


def _make_frame(timecode: float, duration: float, text: str) -> Frame:
    """Create a frame with explicit timecode and duration."""
    frame = Frame()
    frame.timecode = round(timecode * PRECISION)
    frame.duration = round(duration * PRECISION)
    frame.tpe = "o"
    frame.text = text
    return frame


def test_detect_no_similar_frames():
    """Frames with completely different content produce no regions."""
    frames = [
        _make_frame(0.0, 1.0, "hello world"),
        _make_frame(1.0, 1.0, "goodbye world"),
        _make_frame(2.0, 1.0, "something else entirely"),
    ]
    regions = detect_collapse_regions(frames, cols=80, rows=24)
    assert regions == []


def test_detect_identical_frames():
    """Identical consecutive frames form a collapse region."""
    frames = [
        _make_frame(0.0, 1.0, "loading..."),
        _make_frame(1.0, 1.0, "loading..."),
        _make_frame(2.0, 1.0, "loading..."),
        _make_frame(3.0, 1.0, "loading..."),
    ]
    regions = detect_collapse_regions(
        frames, cols=80, rows=24, min_duration=2.0,
    )
    assert len(regions) == 1
    assert regions[0].start_idx == 1
    assert regions[0].end_idx == 4


def test_detect_spinner_pattern():
    """Frames differing by only a spinner char are detected."""
    spinner = ["|", "/", "-", "\\"]
    frames = []
    for i in range(12):
        char = spinner[i % 4]
        frames.append(
            _make_frame(i * 0.5, 0.5, f"\r{char} Processing...")
        )
    regions = detect_collapse_regions(
        frames, cols=80, rows=24, min_duration=2.0,
    )
    assert len(regions) == 1


def test_detect_below_min_duration():
    """Short similar runs below min_duration are not collapsed."""
    frames = [
        _make_frame(0.0, 0.5, "loading..."),
        _make_frame(0.5, 0.5, "loading..."),
        _make_frame(1.0, 1.0, "done!"),
    ]
    regions = detect_collapse_regions(
        frames, cols=80, rows=24, min_duration=2.0,
    )
    assert regions == []


def test_detect_multiple_regions():
    """Multiple separate similar runs are detected independently."""
    frames = [
        # Region 1: spinner
        _make_frame(0.0, 1.0, "spinning |"),
        _make_frame(1.0, 1.0, "spinning /"),
        _make_frame(2.0, 1.0, "spinning -"),
        # Different content
        _make_frame(3.0, 1.0, "Now doing actual work with lots of output"),
        # Region 2: another spinner
        _make_frame(4.0, 1.0, "waiting ."),
        _make_frame(5.0, 1.0, "waiting .."),
        _make_frame(6.0, 1.0, "waiting ..."),
    ]
    regions = detect_collapse_regions(
        frames, cols=80, rows=24, min_duration=1.5,
    )
    assert len(regions) == 2


def test_detect_respects_threshold():
    """Higher threshold allows more change, lower threshold is stricter."""
    frames = [
        _make_frame(0.0, 1.0, "progress: 10%"),
        _make_frame(1.0, 1.0, "progress: 20%"),
        _make_frame(2.0, 1.0, "progress: 30%"),
        _make_frame(3.0, 1.0, "progress: 40%"),
    ]
    # With default threshold (0.05) - small change relative to 80x24 screen
    regions_default = detect_collapse_regions(
        frames, cols=80, rows=24, min_duration=1.5,
    )
    assert len(regions_default) == 1

    # With very strict threshold (0.0) - no change allowed
    regions_strict = detect_collapse_regions(
        frames, cols=80, rows=24, threshold=0.0, min_duration=1.5,
    )
    assert regions_strict == []


def test_detect_index_range():
    """start_idx and end_idx limit detection to a subset of frames."""
    frames = [
        _make_frame(0.0, 1.0, "keep this"),
        _make_frame(1.0, 1.0, "loading..."),
        _make_frame(2.0, 1.0, "loading..."),
        _make_frame(3.0, 1.0, "loading..."),
        _make_frame(4.0, 1.0, "keep this too"),
    ]
    regions = detect_collapse_regions(
        frames, cols=80, rows=24, start_idx=1, end_idx=4, min_duration=1.5,
    )
    assert len(regions) == 1
    assert regions[0].start_idx == 2
    assert regions[0].end_idx == 4
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_collapse.py -v`
Expected: ImportError — `collapse` module does not exist yet

- [ ] **Step 3: Implement `collapse.py`**

Create `src/asciinema_scene/scenelib/collapse.py`:

```python
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
    changed = sum(1 for a, b in zip(prev, current) if a != b)
    return changed / total


def detect_collapse_regions(
    frames: list[Frame],
    cols: int,
    rows: int,
    start_idx: int = 0,
    end_idx: int | None = None,
    threshold: float = 0.05,
    min_duration: float = 2.0,
) -> list[CollapseRegion]:
    """Detect repetitive regions using pyte screen comparison.

    Args:
        frames: List of Frame objects (with timecodes and durations set).
        cols: Terminal width.
        rows: Terminal height.
        start_idx: First frame index to consider (inclusive).
        end_idx: Last frame index to consider (exclusive). None means len(frames).
        threshold: Max change ratio to consider frames "similar" (0.0-1.0).
        min_duration: Minimum region duration in seconds to report.

    Returns:
        List of CollapseRegion describing detected repetitive regions.
    """
    if end_idx is None:
        end_idx = len(frames)
    if end_idx <= start_idx or not frames:
        return []

    screen = pyte.Screen(cols, rows)
    stream = pyte.Stream(screen)

    # Feed all frames before start_idx to build initial screen state
    for frame in frames[:start_idx]:
        if frame.tpe == "o":
            stream.feed(frame.text)

    prev_snapshot = _screen_snapshot(screen)
    run_start: int | None = None
    regions: list[CollapseRegion] = []

    for idx in range(start_idx, end_idx):
        frame = frames[idx]
        if frame.tpe == "o":
            stream.feed(frame.text)
        current_snapshot = _screen_snapshot(screen)
        ratio = _change_ratio(prev_snapshot, current_snapshot)
        is_similar = ratio <= threshold

        if is_similar:
            if run_start is None:
                run_start = idx
        else:
            if run_start is not None:
                _maybe_add_region(
                    regions, frames, run_start, idx, min_duration,
                )
                run_start = None

        prev_snapshot = current_snapshot

    # Close any open run at the end
    if run_start is not None:
        _maybe_add_region(
            regions, frames, run_start, end_idx, min_duration,
        )

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
            )
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_collapse.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run linting and type checking**

Run: `uv run ruff check src/asciinema_scene/scenelib/collapse.py`
Run: `uv run mypy src/asciinema_scene/scenelib/collapse.py`
Expected: No errors. Fix any issues found.

- [ ] **Step 6: Commit**

```bash
git add src/asciinema_scene/scenelib/collapse.py tests/test_collapse.py
git commit -m "feat: add collapse region detection module with tests"
```

---

### Task 3: Add `Scene.collapse()` method with tests

**Files:**
- Modify: `src/asciinema_scene/scenelib/scene.py:1-9` (imports), append method
- Modify: `tests/test_collapse.py` (add integration tests)

- [ ] **Step 1: Write failing tests for `Scene.collapse()`**

Append to `tests/test_collapse.py`:

```python
from asciinema_scene.scenelib.scene import Scene


COLLAPSE_V2_CONTENT = (
    '{"version": 2, "width": 80, "height": 24, "timestamp": 1700000000}\n'
    '[0.0, "o", "starting up"]\n'
    '[1.0, "o", "\\r| loading..."]\n'
    '[2.0, "o", "\\r/ loading..."]\n'
    '[3.0, "o", "\\r- loading..."]\n'
    '[4.0, "o", "\\r\\\\ loading..."]\n'
    '[5.0, "o", "\\r| loading..."]\n'
    '[6.0, "o", "\\r/ loading..."]\n'
    '[7.0, "o", "\\r- loading..."]\n'
    '[8.0, "o", "\\r\\\\ loading..."]\n'
    '[9.0, "o", "\\r| loading..."]\n'
    '[10.0, "o", "\\r/ loading..."]\n'
    '[11.0, "o", "\\rdone!          "]\n'
)


def test_scene_collapse_reduces_duration():
    """Collapse should reduce the duration of the spinner region."""
    scene = Scene()
    scene.parse_content(COLLAPSE_V2_CONTENT)
    orig_duration = scene.duration
    scene.collapse(duration=2.0)
    assert scene.duration < orig_duration


def test_scene_collapse_preserves_frames():
    """Collapse should not remove any frames."""
    scene = Scene()
    scene.parse_content(COLLAPSE_V2_CONTENT)
    orig_count = scene.length
    scene.collapse(duration=2.0)
    assert scene.length == orig_count


def test_scene_collapse_no_similar_noop():
    """If no similar regions exist, duration is unchanged."""
    content = (
        '{"version": 2, "width": 80, "height": 24, "timestamp": 1700000000}\n'
        '[0.0, "o", "hello"]\n'
        '[1.0, "o", "completely different text"]\n'
        '[2.0, "o", "another unique line"]\n'
    )
    scene = Scene()
    scene.parse_content(content)
    orig_duration = scene.duration
    scene.collapse(duration=1.0)
    assert scene.duration == orig_duration


def test_scene_collapse_with_start_end():
    """Collapse respects start/end timecodes."""
    scene = Scene()
    scene.parse_content(COLLAPSE_V2_CONTENT)
    # Only collapse between 2.0 and 8.0
    scene.collapse(duration=1.0, start=2.0, end=8.0)
    # Should still reduce duration but less than full collapse
    assert scene.duration < 12.0


def test_scene_collapse_already_short():
    """Regions already shorter than target duration are untouched."""
    content = (
        '{"version": 2, "width": 80, "height": 24, "timestamp": 1700000000}\n'
        '[0.0, "o", "loading..."]\n'
        '[0.5, "o", "loading..."]\n'
        '[1.0, "o", "loading..."]\n'
        '[1.5, "o", "done!"]\n'
    )
    scene = Scene()
    scene.parse_content(content)
    orig_duration = scene.duration
    # Target 5s but region is only ~1.5s
    scene.collapse(duration=5.0, min_duration=0.5)
    assert scene.duration == orig_duration
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_collapse.py::test_scene_collapse_reduces_duration -v`
Expected: AttributeError — `Scene` has no `collapse` method

- [ ] **Step 3: Implement `Scene.collapse()`**

Add import at top of `src/asciinema_scene/scenelib/scene.py` (after line 8):

```python
from .collapse import detect_collapse_regions
```

Append to the `Scene` class in `src/asciinema_scene/scenelib/scene.py`:

```python
    def collapse(
        self,
        duration: float,
        threshold: float = 0.05,
        min_duration: float = 2.0,
        start: float | None = None,
        end: float | None = None,
    ) -> None:
        """Collapse repetitive/idle regions to at most duration seconds.

        Detects regions where the visible terminal screen barely changes
        and speeds them up so each region takes at most duration seconds.
        """
        if duration <= 0.0:
            raise ValueError(duration)
        self.pre_normalize()
        tcode_start, tcode_end = self.start_end(start, end)
        idx1, idx2 = self._split_parts(tcode_start, tcode_end)
        cols = self.header.get("width", 80)
        rows = self.header.get("height", 24)
        regions = detect_collapse_regions(
            self.frames,
            cols=cols,
            rows=rows,
            start_idx=idx1,
            end_idx=idx2,
            threshold=threshold,
            min_duration=min_duration,
        )
        target_duration_tc = round(duration * PRECISION)
        for region in regions:
            region_duration_tc = 0
            for frame in self.frames[region.start_idx : region.end_idx]:
                region_duration_tc += frame.duration
            if region_duration_tc <= target_duration_tc:
                continue
            factor = target_duration_tc / region_duration_tc
            for frame in self.frames[region.start_idx : region.end_idx]:
                frame.duration = round(frame.duration * factor)
        self.set_timecodes()
        self.post_normalize()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_collapse.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run linting and type checking**

Run: `uv run ruff check src/asciinema_scene/scenelib/scene.py`
Run: `uv run mypy src/asciinema_scene/scenelib/scene.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add src/asciinema_scene/scenelib/scene.py tests/test_collapse.py
git commit -m "feat: add Scene.collapse() method with tests"
```

---

### Task 4: Add `collapse` CLI command

**Files:**
- Modify: `src/asciinema_scene/sciine.py` (append command after `text_merge_cmd`)

- [ ] **Step 1: Add the CLI command**

Append to `src/asciinema_scene/sciine.py`, before the `convert` command (before line 595):

```python
@cli.command("collapse")
@stdin_timeout_handler
@click.argument("duration", required=True, type=float)
@start_option
@end_option
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=0.05,
    show_default=True,
    help="Max screen change ratio to consider 'similar' (0.0-1.0).",
)
@click.option(
    "--min-duration",
    "-m",
    type=float,
    default=2.0,
    show_default=True,
    help="Minimum region duration (seconds) to collapse.",
)
@format_option
@input_option
@output_option
def collapse_cmd(
    duration: float,
    start: float | None,
    end: float | None,
    threshold: float,
    min_duration: float,
    output_format: str | None,
    input_file: str | None,
    output_file: str | None,
) -> None:
    """Collapse repetitive/idle regions to at most DURATION seconds each.

    Detects regions where the visible terminal screen barely changes
    (spinners, progress bars, AI thinking indicators) and speeds them
    up so each region takes at most DURATION seconds.
    """
    scene = Scene.parse(input_file)
    scene.collapse(
        duration,
        threshold=threshold,
        min_duration=min_duration,
        start=start,
        end=end,
    )
    if output_format:
        version = int(output_format[1])
        scene.set_format_version(version)
    scene.dump(output_file)
```

- [ ] **Step 2: Verify the command is registered**

Run: `uv run sciine --help`
Expected: `collapse` appears in the command list

Run: `uv run sciine collapse --help`
Expected: Shows help with DURATION argument, --threshold, --min-duration options

- [ ] **Step 3: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests pass including existing ones

- [ ] **Step 4: Run linting and type checking on all modified files**

Run: `uv run ruff check src/asciinema_scene/sciine.py`
Run: `uv run mypy`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add src/asciinema_scene/sciine.py
git commit -m "feat: add collapse CLI command"
```

---

### Task 5: Add v3 format and edge case tests

**Files:**
- Modify: `tests/test_collapse.py` (add more tests)

- [ ] **Step 1: Write v3 format and edge case tests**

Append to `tests/test_collapse.py`:

```python
COLLAPSE_V3_CONTENT = (
    '{"version": 3, "term": {"cols": 80, "rows": 24}, "timestamp": 1700000000}\n'
    '[0.0, "o", "starting up"]\n'
    '[1.0, "o", "\\r| loading..."]\n'
    '[1.0, "o", "\\r/ loading..."]\n'
    '[1.0, "o", "\\r- loading..."]\n'
    '[1.0, "o", "\\r\\\\ loading..."]\n'
    '[1.0, "o", "\\r| loading..."]\n'
    '[1.0, "o", "\\r/ loading..."]\n'
    '[1.0, "o", "\\r- loading..."]\n'
    '[1.0, "o", "\\r\\\\ loading..."]\n'
    '[1.0, "o", "\\r| loading..."]\n'
    '[1.0, "o", "\\r/ loading..."]\n'
    '[1.0, "o", "\\rdone!          "]\n'
)


def test_scene_collapse_v3_format():
    """Collapse works with v3 format recordings."""
    scene = Scene()
    scene.parse_content(COLLAPSE_V3_CONTENT)
    orig_duration = scene.duration
    scene.collapse(duration=2.0)
    assert scene.duration < orig_duration


def test_scene_collapse_v3_preserves_format():
    """Collapse preserves v3 format version."""
    scene = Scene()
    scene.parse_content(COLLAPSE_V3_CONTENT)
    scene.collapse(duration=2.0)
    assert scene.format_version == 3


def test_scene_collapse_invalid_duration():
    """Collapse raises ValueError for non-positive duration."""
    import pytest

    scene = Scene()
    scene.parse_content(COLLAPSE_V2_CONTENT)
    with pytest.raises(ValueError):
        scene.collapse(duration=0.0)
    with pytest.raises(ValueError):
        scene.collapse(duration=-1.0)


def test_detect_input_frames_only():
    """Input event frames (type 'i') are not fed to screen emulator."""
    frames = [
        _make_frame(0.0, 1.0, "visible output"),
        _make_frame(1.0, 1.0, "visible output"),
        _make_frame(2.0, 1.0, "visible output"),
    ]
    # Set one frame to input type
    frames[1].tpe = "i"
    frames[1].text = "keystroke"
    regions = detect_collapse_regions(
        frames, cols=80, rows=24, min_duration=1.5,
    )
    # Should still detect similarity (input frame is skipped for screen)
    assert len(regions) == 1
```

- [ ] **Step 2: Run all tests**

Run: `uv run pytest tests/test_collapse.py -v`
Expected: All tests PASS

- [ ] **Step 3: Run full project checks**

Run: `uv run ruff check src`
Run: `uv run mypy`
Run: `uv run pytest`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add tests/test_collapse.py
git commit -m "test: add v3 format and edge case tests for collapse"
```
