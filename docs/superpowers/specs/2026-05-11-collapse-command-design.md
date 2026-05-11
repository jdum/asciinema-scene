# Collapse Command Design

## Purpose

Detect and compress repetitive/idle regions in asciinema recordings where the visible terminal screen barely changes (spinners, progress bars, AI thinking indicators). Each detected region is sped up to fit within a user-specified maximum duration.

## CLI Interface

```
sciine collapse [OPTIONS] DURATION

  Collapse repetitive/idle regions to at most DURATION seconds each.

Options:
  -s, --start TIMECODE    Start timecode, default is 0.0
  -e, --end TIMECODE      End timecode, default is EOF
  -t, --threshold FLOAT   Max screen change ratio to consider "similar" (0.0-1.0, default 0.05)
  -m, --min-duration FLOAT  Minimum region duration in seconds to collapse (default 2.0)
  -f, --format [v2|v3]    Output format
  -i, --input PATH        Input .cast file
  -o, --output PATH       Output .cast file
```

### Examples

```bash
# Collapse all detected waiting regions to at most 3 seconds each
sciine collapse 3 -i recording.cast -o edited.cast

# Only collapse regions in the first 2 minutes, with stricter similarity
sciine collapse 2 -s 0 -e 2:00 -t 0.02 -i recording.cast -o edited.cast

# Pipe-friendly
cat recording.cast | sciine collapse 3 > edited.cast
```

## Algorithm

### Step 1: Screen Emulation

Use `pyte` to maintain a virtual terminal screen buffer matching the recording dimensions (`cols` x `rows` from header).

- Create `pyte.Screen(cols, rows)` and `pyte.Stream()` connected to it.
- For each frame, feed its text content into the stream via `stream.feed()`.
- After each frame, capture the screen state as a flat string: join all screen lines.

### Step 2: Similarity Comparison

Compare consecutive screen snapshots:

- Count cells that differ between current and previous snapshot.
- Compute `change_ratio = changed_cells / total_cells`.
- If `change_ratio <= threshold` (default 0.05), the frame is "similar" to its predecessor.

### Step 3: Region Detection

Build contiguous runs of "similar" frames:

- Walk through all frames in the selected range.
- Accumulate consecutive "similar" frames into runs.
- A "non-similar" frame breaks the current run.
- Discard runs whose total duration is below `min_duration` (default 2.0s).
- Each surviving run is a "collapse region," defined by its start and end frame indices and its total duration.

### Step 4: Speed Adjustment

For each collapse region:

- If region duration `D <= DURATION`, skip (already short enough).
- Otherwise, compute `speed_factor = D / DURATION`.
- Multiply each frame's duration in the region by `1 / speed_factor` (same as `scene.speed()`).

### Step 5: Finalize

Call `set_timecodes()` to recompute absolute timecodes from the modified durations.

## Architecture

### New file: `src/asciinema_scene/scenelib/collapse.py`

Contains the detection logic, isolated from core scene code:

```python
@dataclass
class CollapseRegion:
    start_idx: int
    end_idx: int
    duration: float  # in seconds

def detect_collapse_regions(
    frames: list[Frame],
    cols: int,
    rows: int,
    start_idx: int,
    end_idx: int,
    threshold: float = 0.05,
    min_duration: float = 2.0,
) -> list[CollapseRegion]:
    """Detect repetitive regions using pyte screen comparison."""
```

### Scene method: `scene.py`

```python
def collapse(
    self,
    duration: float,
    threshold: float = 0.05,
    min_duration: float = 2.0,
    start: float | None = None,
    end: float | None = None,
) -> None:
```

Follows the standard pattern: `pre_normalize()`, detect regions via `collapse.py`, apply speed adjustment per region, `set_timecodes()`, `post_normalize()`.

### CLI command: `sciine.py`

Standard Click command following existing patterns. Uses `@click.argument("duration")` plus `@start_option`, `@end_option`, `@format_option`, `@input_option`, `@output_option`, plus two new options for `--threshold` and `--min-duration`.

### Dependency: `pyte`

Add `pyte` to `[project.dependencies]` in `pyproject.toml`.

## Parameters

| Parameter | Default | Rationale |
|-----------|---------|-----------|
| `DURATION` (arg) | required | Target max duration per collapsed region |
| `--threshold` | 0.05 | 5% screen change allows spinner chars, progress increments, counter updates |
| `--min-duration` | 2.0 | Prevents collapsing brief natural pauses |

## Edge Cases

- **No regions detected**: Output is identical to input.
- **Region already shorter than DURATION**: Skipped, no speed change.
- **Entire recording is one region**: Collapses the whole thing.
- **Multiple regions**: Each handled independently with its own speed factor.
- **Frames outside regions**: Untouched.
- **Header missing dimensions**: Fall back to default 80x24.

## Testing

- Unit tests for `detect_collapse_regions()` with synthetic frame data containing known spinner patterns.
- Integration tests for `scene.collapse()` verifying duration reduction.
- CLI tests for argument parsing and pipe support.
- Tests with both v2 and v3 format recordings.
- Test that frames outside collapse regions are unmodified.
- Test `min_duration` filtering (short similar runs ignored).
- Test `threshold` sensitivity (higher threshold collapses more, lower less).
