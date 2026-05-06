# asciicast v3 Format Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add full bidirectional asciicast v3 format support with auto-detection, format preservation, and a `convert` command.

**Architecture:** Single internal model with absolute-timecode representation (unchanged). Format-version-aware parsing converts v3 relative intervals to absolute timecodes on input. Serialization converts back to relative intervals for v3 output. A `format_version` field on `SceneContent` tracks the detected/desired format.

**Tech Stack:** Python 3.10+, Click (CLI), json (stdlib), pytest (testing), mypy (strict typing)

---

### Task 1: Add v3 Test Sample File

**Files:**
- Create: `tests/files/short_v3.cast`
- Modify: `tests/contents.py`

This is the equivalent of `tests/files/short.cast` but in v3 format. Same terminal content, relative intervals instead of absolute timecodes.

- [ ] **Step 1: Create v3 sample cast file**

Create `tests/files/short_v3.cast` — the same recording as `short.cast` converted to v3 format:

```json
{"version": 3, "term": {"cols": 133, "rows": 36, "type": "linux"}, "timestamp": 1685272506, "env": {"SHELL": "/bin/bash"}}
[0.01, "o", "e"]
[0.894, "o", "c"]
[0.105, "o", "h"]
[0.165, "o", "o"]
[0.301, "o", " "]
[0.392, "o", "\""]
[0.357, "o", "a"]
[0.15, "o", " "]
[0.511, "o", "s"]
[0.238, "o", "h"]
[0.367, "o", "o"]
[0.204, "o", "r"]
[0.165, "o", "t"]
[0.134, "o", " "]
[0.211, "o", "t"]
[0.18, "o", "e"]
[0.215, "o", "s"]
[0.161, "o", "t"]
[0.194, "o", "\""]
[0.451, "o", "\r\n\u001b[?2004l\r"]
[0.0, "o", "a short test\r\n"]
[0.742, "o", "\r\n"]
```

Note: Intervals are computed as deltas between consecutive absolute timecodes from `short.cast`, rounded to 3 decimal places (millisecond precision per v3 spec).

- [ ] **Step 2: Add v3 content reference to tests/contents.py**

Add to `tests/contents.py`:

```python
SHORT_V3_FILE_CONTENT = (
    rso.files("tests.files").joinpath("short_v3.cast").read_text(encoding="utf8")
)
```

- [ ] **Step 3: Commit**

```bash
git add tests/files/short_v3.cast tests/contents.py
git commit -m "test: add v3 sample cast file for testing"
```

---

### Task 2: Add `format_version` to SceneContent and Update Parsing for v3

**Files:**
- Modify: `src/asciinema_scene/scenelib/scene_content.py`
- Create: `tests/test_v3_parse.py`

- [ ] **Step 1: Write failing test for v3 parsing**

Create `tests/test_v3_parse.py`:

```python
from asciinema_scene.scenelib import SceneContent
from contents import SHORT_V3_FILE_CONTENT


def test_v3_parse_detects_version():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    assert scene.format_version == 3


def test_v3_parse_header_extracts_dimensions():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    assert scene.header["width"] == 133
    assert scene.header["height"] == 36


def test_v3_parse_converts_intervals_to_absolute_timecodes():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    # First frame: interval 0.01 -> timecode 0.01
    assert scene.frames[0].tc_float == 0.01
    # Second frame: interval 0.894 -> timecode 0.01 + 0.894 = 0.904
    assert abs(scene.frames[1].tc_float - 0.904) < 0.001


def test_v3_parse_frame_count_matches_v2():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    # 22 data lines + 1 trailing \r\n from pre_normalize = 23 frames
    # (same count as short.cast after pre_normalize)
    assert scene.length == 23


def test_v3_parse_skips_comment_lines():
    content = '{"version": 3, "term": {"cols": 80, "rows": 24}}\n# this is a comment\n[0.5, "o", "hi"]\n'
    scene = SceneContent()
    scene.parse_content(content)
    assert scene.format_version == 3
    assert scene.length == 2  # 1 frame + 1 trailing \r\n from pre_normalize
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_v3_parse.py -v`
Expected: FAIL — `AttributeError: 'SceneContent' object has no attribute 'format_version'`

- [ ] **Step 3: Implement v3 parsing in SceneContent**

Modify `src/asciinema_scene/scenelib/scene_content.py`:

1. Add `format_version` field in `__init__`:

```python
def __init__(self) -> None:
    self.input_file: str = "string"
    self.header: dict[str, Any] = {}
    self.frames: list[Frame] = []
    self.format_version: int = 2
```

2. Replace `parse_content` method:

```python
def parse_content(self, raw_content: str) -> None:
    for line in raw_content.split("\n"):
        if not line:
            continue
        if line.startswith("#"):
            continue
        frame = self._decode(line)
        if isinstance(frame, list):
            self.frames.append(Frame.parse(frame))
            continue
        if not self.header and isinstance(frame, dict):
            self.header = frame
    self._detect_and_normalize_format()
    self.pre_normalize()

def _detect_and_normalize_format(self) -> None:
    version = self.header.get("version", 2)
    self.format_version = version
    if version == 3:
        self._convert_v3_header()
        self._convert_intervals_to_timecodes()

def _convert_v3_header(self) -> None:
    """Convert v3 header schema to internal representation."""
    term = self.header.get("term", {})
    # Store original v3 header for round-trip
    self.header["_v3_term"] = term.copy()
    # Extract dimensions to top-level for internal use
    self.header["width"] = term.get("cols", 80)
    self.header["height"] = term.get("rows", 24)
    # version stays as-is

def _convert_intervals_to_timecodes(self) -> None:
    """Convert v3 relative intervals to absolute timecodes."""
    cumulative = 0
    for frame in self.frames:
        cumulative += frame.timecode
        frame.timecode = cumulative
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_v3_parse.py -v`
Expected: All PASS

- [ ] **Step 5: Run full test suite to check no regressions**

Run: `uv run pytest`
Expected: All existing tests PASS

- [ ] **Step 6: Run linting and type checking**

Run: `uv run ruff check src && uv run mypy`
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add src/asciinema_scene/scenelib/scene_content.py tests/test_v3_parse.py
git commit -m "feat: add v3 format detection and parsing with interval-to-timecode conversion"
```

---

### Task 3: Add v3 Serialization

**Files:**
- Modify: `src/asciinema_scene/scenelib/scene_content.py`
- Create: `tests/test_v3_serialize.py`

- [ ] **Step 1: Write failing test for v3 serialization**

Create `tests/test_v3_serialize.py`:

```python
import json

from asciinema_scene.scenelib import SceneContent
from contents import SHORT_V3_FILE_CONTENT


def test_v3_dumps_produces_v3_header():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    output = scene.dumps()
    header = json.loads(output.split("\n")[0])
    assert header["version"] == 3
    assert "term" in header
    assert header["term"]["cols"] == 133
    assert header["term"]["rows"] == 36


def test_v3_dumps_uses_relative_intervals():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    output = scene.dumps()
    lines = output.strip().split("\n")
    # First event line
    event1 = json.loads(lines[1])
    # Should be the interval (relative time), not absolute
    # After pre_normalize, t0 is normalized to 0, first frame timecode = 0
    assert event1[0] == 0.0
    # Second event: should be interval from first to second
    event2 = json.loads(lines[2])
    assert event2[0] > 0


def test_v3_round_trip_preserves_content():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    output = scene.dumps()
    # Re-parse the output
    scene2 = SceneContent()
    scene2.parse_content(output)
    assert scene2.format_version == 3
    assert scene2.length == scene.length
    # Timecodes should match within microsecond precision
    for f1, f2 in zip(scene.frames, scene2.frames):
        assert abs(f1.timecode - f2.timecode) <= 1
        assert f1.tpe == f2.tpe
        assert f1.text == f2.text


def test_v3_header_no_width_height_top_level():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    output = scene.dumps()
    header = json.loads(output.split("\n")[0])
    assert "width" not in header
    assert "height" not in header


def test_v3_header_preserves_env():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    output = scene.dumps()
    header = json.loads(output.split("\n")[0])
    assert header["env"] == {"SHELL": "/bin/bash"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_v3_serialize.py -v`
Expected: FAIL — dumps() still produces v2 format

- [ ] **Step 3: Implement v3 serialization**

Modify `src/asciinema_scene/scenelib/scene_content.py`. Replace the `dumps` method:

```python
def dumps(self, format_version: int | None = None) -> str:
    version = format_version if format_version is not None else self.format_version
    if version == 3:
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
    v3_term = self.header.get("_v3_term", {})
    term: dict[str, Any] = {
        "cols": self.header.get("width", 80),
        "rows": self.header.get("height", 24),
    }
    # Preserve term.type
    if "type" in v3_term:
        term["type"] = v3_term["type"]
    elif "env" in self.header and "TERM" in self.header.get("env", {}):
        term["type"] = self.header["env"]["TERM"]
    # Preserve term.version
    if "version" in v3_term:
        term["version"] = v3_term["version"]
    # Preserve term.theme
    if "theme" in v3_term:
        term["theme"] = v3_term["theme"]
    elif "theme" in self.header:
        term["theme"] = self.header["theme"]

    header: dict[str, Any] = {"version": 3, "term": term}
    # Copy other fields
    for key in ("timestamp", "idle_time_limit", "command", "title", "env", "tags"):
        if key in self.header:
            header[key] = self.header[key]
    return header
```

Also add the PRECISION import at the top of the file:

```python
from .constants import PRECISION
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_v3_serialize.py -v`
Expected: All PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest`
Expected: All PASS

- [ ] **Step 6: Run linting and type checking**

Run: `uv run ruff check src && uv run mypy`
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add src/asciinema_scene/scenelib/scene_content.py tests/test_v3_serialize.py
git commit -m "feat: add v3 serialization with timecode-to-interval conversion"
```

---

### Task 4: Add `convert` CLI Command

**Files:**
- Modify: `src/asciinema_scene/sciine.py`
- Create: `tests/test_convert.py`

- [ ] **Step 1: Write failing test for convert command**

Create `tests/test_convert.py`:

```python
import json

from click.testing import CliRunner

from asciinema_scene.sciine import cli
from contents import SHORT_FILE_CONTENT, SHORT_V3_FILE_CONTENT


def test_convert_v2_to_v3():
    runner = CliRunner()
    result = runner.invoke(cli, ["convert", "--format", "v3"], input=SHORT_FILE_CONTENT)
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    header = json.loads(lines[0])
    assert header["version"] == 3
    assert "term" in header
    assert header["term"]["cols"] == 133
    # Events should have relative intervals
    event1 = json.loads(lines[1])
    assert event1[0] == 0.0  # first frame after t0 normalization


def test_convert_v3_to_v2():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["convert", "--format", "v2"], input=SHORT_V3_FILE_CONTENT
    )
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    header = json.loads(lines[0])
    assert header["version"] == 2
    assert header["width"] == 133
    assert header["height"] == 36
    # Events should have absolute timecodes
    event1 = json.loads(lines[1])
    assert event1[0] == 0.0  # first frame (t0 normalized)


def test_convert_requires_format_option():
    runner = CliRunner()
    result = runner.invoke(cli, ["convert"], input=SHORT_FILE_CONTENT)
    assert result.exit_code != 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_convert.py -v`
Expected: FAIL — `No such command 'convert'`

- [ ] **Step 3: Implement convert command**

Add to `src/asciinema_scene/sciine.py`, after the existing commands:

```python
@cli.command("convert")
@stdin_timeout_handler
@click.option(
    "--format",
    "-f",
    "output_format",
    required=True,
    type=click.Choice(["v2", "v3"]),
    help="Output format version.",
)
@input_option
@output_option
def convert_cmd(
    output_format: str,
    input_file: str | None,
    output_file: str | None,
) -> None:
    """Convert between asciicast v2 and v3 formats.

    Reads input in any supported format (auto-detected) and writes
    output in the specified format.
    """
    scene = Scene.parse(input_file)
    version = int(output_format[1])  # "v2" -> 2, "v3" -> 3
    scene.set_format_version(version)
    scene.dump(output_file)
```

- [ ] **Step 4: Add `set_format_version` public method to SceneContent**

Add to `src/asciinema_scene/scenelib/scene_content.py`:

```python
def set_format_version(self, version: int) -> None:
    """Set the output format version and adjust header accordingly."""
    self.format_version = version
    if version == 2:
        self._build_v2_header()

def _build_v2_header(self) -> None:
    """Convert internal header to v2 schema in-place."""
    self.header["version"] = 2
    # Ensure width/height at top level
    if "_v3_term" in self.header:
        v3_term = self.header.pop("_v3_term")
        # Move term.type to env.TERM
        if "type" in v3_term:
            env = self.header.setdefault("env", {})
            env.setdefault("TERM", v3_term["type"])
        # Move term.theme to top-level theme
        if "theme" in v3_term:
            self.header.setdefault("theme", v3_term["theme"])
    # Remove v3-only fields
    self.header.pop("tags", None)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_convert.py -v`
Expected: All PASS

- [ ] **Step 6: Run full test suite**

Run: `uv run pytest`
Expected: All PASS

- [ ] **Step 7: Run linting and type checking**

Run: `uv run ruff check src && uv run mypy`
Expected: No errors

- [ ] **Step 8: Commit**

```bash
git add src/asciinema_scene/sciine.py src/asciinema_scene/scenelib/scene_content.py tests/test_convert.py
git commit -m "feat: add convert command for v2/v3 format conversion"
```

---

### Task 5: Add `--format` Option to All Output Commands

**Files:**
- Modify: `src/asciinema_scene/sciine.py`
- Create: `tests/test_format_option.py`

- [ ] **Step 1: Write failing test for --format option**

Create `tests/test_format_option.py`:

```python
import json

from click.testing import CliRunner

from asciinema_scene.sciine import cli
from contents import SHORT_FILE_CONTENT, SHORT_V3_FILE_CONTENT


def test_cut_preserves_v3_format():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["cut", "--start", "1.0", "--end", "2.0"], input=SHORT_V3_FILE_CONTENT
    )
    assert result.exit_code == 0
    header = json.loads(result.output.split("\n")[0])
    assert header["version"] == 3


def test_cut_with_format_v3_converts_v2_input():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["cut", "--start", "1.0", "--end", "2.0", "--format", "v3"],
        input=SHORT_FILE_CONTENT,
    )
    assert result.exit_code == 0
    header = json.loads(result.output.split("\n")[0])
    assert header["version"] == 3


def test_speed_preserves_v2_format():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["speed", "2.0"], input=SHORT_FILE_CONTENT
    )
    assert result.exit_code == 0
    header = json.loads(result.output.split("\n")[0])
    assert header["version"] == 2


def test_speed_with_format_v2_from_v3_input():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["speed", "2.0", "--format", "v2"], input=SHORT_V3_FILE_CONTENT
    )
    assert result.exit_code == 0
    header = json.loads(result.output.split("\n")[0])
    assert header["version"] == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_format_option.py -v`
Expected: FAIL — `no such option: --format` (for commands other than convert)

- [ ] **Step 3: Implement shared --format option**

Modify `src/asciinema_scene/sciine.py`:

1. Add a shared option decorator near the other option definitions (after `adjust_option`):

```python
format_option = click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["v2", "v3"]),
    default=None,
    help="Output format (v2 or v3). Default: preserve input format.",
)
```

2. Add `format_option` decorator and `output_format` parameter to all commands that call `scene.dump()`: `cut_cmd`, `copy_cmd`, `speed_cmd`, `maximum_cmd`, `minimum_cmd`, `quantize_cmd`, `insert_cmd`, `delete_cmd`, `replace_cmd`, `include_cmd`, `text_delete_cmd`, `text_replace_cmd`, `text_merge_cmd`.

3. Before each `scene.dump(output_file)` call, add format handling:

```python
if output_format:
    version = int(output_format[1])
    scene.set_format_version(version)
```

For example, `cut_cmd` becomes:

```python
@cli.command("cut")
@stdin_timeout_handler
@start_option
@end_option
@adjust_option
@format_option
@input_option
@output_option
def cut_cmd(
    start: float | None,
    end: float | None,
    adjust: bool,
    output_format: str | None,
    input_file: str | None,
    output_file: str | None,
) -> None:
    """Cut content between START and END timecodes.

    If no START timecode is provided, cut from the beginning. If no END
    timecode is provided, cut until the end.
    """
    scene = Scene.parse(input_file)
    scene.cut_frames(start=start, end=end, adjust=adjust)
    if output_format:
        version = int(output_format[1])
        scene.set_format_version(version)
    scene.dump(output_file)
```

Apply the same pattern to all other output commands.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_format_option.py -v`
Expected: All PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest`
Expected: All PASS

- [ ] **Step 6: Run linting and type checking**

Run: `uv run ruff check src && uv run mypy`
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add src/asciinema_scene/sciine.py tests/test_format_option.py
git commit -m "feat: add --format option to all output commands for format selection"
```

---

### Task 6: Add v3 Integration Tests for All Existing Commands

**Files:**
- Create: `tests/test_v3_commands.py`

- [ ] **Step 1: Write integration tests**

Create `tests/test_v3_commands.py`:

```python
"""Integration tests: all existing commands work correctly with v3 input."""
import json

from click.testing import CliRunner

from asciinema_scene.sciine import cli
from contents import SHORT_V3_FILE_CONTENT


def _get_header(output: str) -> dict:
    return json.loads(output.split("\n")[0])


def _get_events(output: str) -> list:
    lines = output.strip().split("\n")
    return [json.loads(line) for line in lines[1:] if line]


def test_status_with_v3():
    runner = CliRunner()
    result = runner.invoke(cli, ["status"], input=SHORT_V3_FILE_CONTENT)
    assert result.exit_code == 0
    assert "Frames:" in result.output
    assert "Duration:" in result.output


def test_header_with_v3():
    runner = CliRunner()
    result = runner.invoke(cli, ["header"], input=SHORT_V3_FILE_CONTENT)
    assert result.exit_code == 0
    assert "width" in result.output or "cols" in result.output


def test_show_with_v3():
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "--lines", "5"], input=SHORT_V3_FILE_CONTENT)
    assert result.exit_code == 0
    # Should show timecode/duration/text lines
    assert "\u2502" in result.output  # pipe separator used in show


def test_cut_with_v3():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["cut", "--start", "1.0", "--end", "3.0"], input=SHORT_V3_FILE_CONTENT
    )
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3


def test_copy_with_v3():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["copy", "--start", "1.0", "--end", "3.0"], input=SHORT_V3_FILE_CONTENT
    )
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3


def test_speed_with_v3():
    runner = CliRunner()
    result = runner.invoke(cli, ["speed", "2.0"], input=SHORT_V3_FILE_CONTENT)
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3


def test_maximum_with_v3():
    runner = CliRunner()
    result = runner.invoke(cli, ["maximum", "0.5"], input=SHORT_V3_FILE_CONTENT)
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3


def test_minimum_with_v3():
    runner = CliRunner()
    result = runner.invoke(cli, ["minimum", "0.1"], input=SHORT_V3_FILE_CONTENT)
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3


def test_quantize_with_v3():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["quantize", "0.1", "0.5", "0.2"], input=SHORT_V3_FILE_CONTENT
    )
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3


def test_text_delete_with_v3():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["text-delete", "short"], input=SHORT_V3_FILE_CONTENT
    )
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3


def test_text_replace_with_v3():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["text-replace", "short", "long"], input=SHORT_V3_FILE_CONTENT
    )
    assert result.exit_code == 0
    header = _get_header(result.output)
    assert header["version"] == 3
```

- [ ] **Step 2: Run tests**

Run: `uv run pytest tests/test_v3_commands.py -v`
Expected: All PASS (the implementation from previous tasks should handle these)

- [ ] **Step 3: Run full test suite**

Run: `uv run pytest`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_v3_commands.py
git commit -m "test: add v3 integration tests for all existing commands"
```

---

### Task 7: Handle v3 Header Conversion for `convert` (v2→v3 direction)

**Files:**
- Modify: `src/asciinema_scene/scenelib/scene_content.py`
- Modify: `tests/test_convert.py`

- [ ] **Step 1: Write failing test for v2→v3 header translation**

Add to `tests/test_convert.py`:

```python
def test_convert_v2_to_v3_maps_env_term_to_term_type():
    runner = CliRunner()
    result = runner.invoke(cli, ["convert", "--format", "v3"], input=SHORT_FILE_CONTENT)
    assert result.exit_code == 0
    header = json.loads(result.output.split("\n")[0])
    # short.cast has env.TERM = "linux"
    assert header["term"]["type"] == "linux"
    # TERM should not be duplicated in env
    if "env" in header:
        assert "TERM" not in header["env"]


def test_convert_v3_to_v2_maps_term_type_to_env_term():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["convert", "--format", "v2"], input=SHORT_V3_FILE_CONTENT
    )
    assert result.exit_code == 0
    header = json.loads(result.output.split("\n")[0])
    assert header["env"]["TERM"] == "linux"
    assert "term" not in header
    assert "_v3_term" not in header
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_convert.py::test_convert_v2_to_v3_maps_env_term_to_term_type tests/test_convert.py::test_convert_v3_to_v2_maps_term_type_to_env_term -v`
Expected: FAIL

- [ ] **Step 3: Update `_build_v3_header` to handle v2→v3 TERM promotion**

In `src/asciinema_scene/scenelib/scene_content.py`, update `_build_v3_header`:

The existing implementation already handles `env.TERM` → `term.type`. We need to also remove TERM from the env dict in v3 output. Update the `_build_v3_header` method:

```python
def _build_v3_header(self) -> dict[str, Any]:
    """Build v3 header from internal representation."""
    v3_term = self.header.get("_v3_term", {})
    term: dict[str, Any] = {
        "cols": self.header.get("width", 80),
        "rows": self.header.get("height", 24),
    }
    # Preserve term.type or promote from env.TERM
    if "type" in v3_term:
        term["type"] = v3_term["type"]
    elif "env" in self.header and "TERM" in self.header.get("env", {}):
        term["type"] = self.header["env"]["TERM"]
    # Preserve term.version
    if "version" in v3_term:
        term["version"] = v3_term["version"]
    # Preserve term.theme or promote from top-level theme
    if "theme" in v3_term:
        term["theme"] = v3_term["theme"]
    elif "theme" in self.header:
        term["theme"] = self.header["theme"]

    header: dict[str, Any] = {"version": 3, "term": term}
    # Copy other fields
    for key in ("timestamp", "idle_time_limit", "command", "title", "tags"):
        if key in self.header:
            header[key] = self.header[key]
    # Copy env without TERM (it's been promoted to term.type)
    if "env" in self.header:
        env = {k: v for k, v in self.header["env"].items() if k != "TERM"}
        if env:
            header["env"] = env
    return header
```

Also ensure `_build_v2_header` removes `_v3_term` and doesn't leave `term` in the output (it already does via the pop). Also ensure `_dumps_v2` filters out internal keys:

The `_dumps_v2` method already filters keys starting with `_`. Also ensure it doesn't include `term` or `tags`:

```python
def _dumps_v2(self) -> str:
    content = []
    header = {
        k: v for k, v in self.header.items()
        if not k.startswith("_") and k not in ("term", "tags")
    }
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_convert.py -v`
Expected: All PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest`
Expected: All PASS

- [ ] **Step 6: Run linting and type checking**

Run: `uv run ruff check src && uv run mypy`
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add src/asciinema_scene/scenelib/scene_content.py tests/test_convert.py
git commit -m "feat: complete v2/v3 header translation for convert command"
```

---

### Task 8: Handle All v3 Event Types (`m`, `r`, `x`)

**Files:**
- Create: `tests/test_v3_event_types.py`

The `Frame` class already supports arbitrary `tpe` strings, and `match()`/`replace()` already guard on `tpe == "o"`. This task verifies that `m`, `r`, `x` events are properly preserved through parsing, operations, and serialization.

- [ ] **Step 1: Write tests for v3 event types**

Create `tests/test_v3_event_types.py`:

```python
import json

from asciinema_scene.scenelib import SceneContent


V3_WITH_ALL_EVENTS = """\
{"version": 3, "term": {"cols": 80, "rows": 24}}
[0.5, "o", "hello"]
[1.0, "m", "chapter1"]
[0.5, "o", " world"]
[2.0, "r", "100x50"]
[1.0, "o", "bye"]
[0.5, "x", "0"]
"""


def test_parse_marker_event():
    scene = SceneContent()
    scene.parse_content(V3_WITH_ALL_EVENTS)
    markers = [f for f in scene.frames if f.tpe == "m"]
    assert len(markers) == 1
    assert markers[0].text == "chapter1"


def test_parse_resize_event():
    scene = SceneContent()
    scene.parse_content(V3_WITH_ALL_EVENTS)
    resizes = [f for f in scene.frames if f.tpe == "r"]
    assert len(resizes) == 1
    assert resizes[0].text == "100x50"


def test_parse_exit_event():
    scene = SceneContent()
    scene.parse_content(V3_WITH_ALL_EVENTS)
    exits = [f for f in scene.frames if f.tpe == "x"]
    assert len(exits) == 1
    assert exits[0].text == "0"


def test_round_trip_preserves_all_event_types():
    scene = SceneContent()
    scene.parse_content(V3_WITH_ALL_EVENTS)
    output = scene.dumps()
    scene2 = SceneContent()
    scene2.parse_content(output)
    types_original = [f.tpe for f in scene.frames]
    types_roundtrip = [f.tpe for f in scene2.frames]
    assert types_original == types_roundtrip


def test_serialize_all_event_types_as_v3():
    scene = SceneContent()
    scene.parse_content(V3_WITH_ALL_EVENTS)
    output = scene.dumps()
    lines = output.strip().split("\n")
    events = [json.loads(line) for line in lines[1:]]
    types = [e[1] for e in events]
    assert "m" in types
    assert "r" in types
    assert "x" in types
    assert "o" in types
```

- [ ] **Step 2: Run tests**

Run: `uv run pytest tests/test_v3_event_types.py -v`
Expected: All PASS (Frame already handles arbitrary tpe strings)

- [ ] **Step 3: Commit**

```bash
git add tests/test_v3_event_types.py
git commit -m "test: verify all v3 event types (m, r, x) are preserved through operations"
```

---

### Task 9: Update `duplicate()` and Ensure `format_version` Propagation

**Files:**
- Modify: `src/asciinema_scene/scenelib/scene_content.py`
- Create: `tests/test_v3_duplicate.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_v3_duplicate.py`:

```python
from asciinema_scene.scenelib import SceneContent
from contents import SHORT_V3_FILE_CONTENT


def test_duplicate_preserves_format_version():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    dup = scene.duplicate()
    assert dup.format_version == 3


def test_duplicate_v3_produces_v3_output():
    scene = SceneContent()
    scene.parse_content(SHORT_V3_FILE_CONTENT)
    dup = scene.duplicate()
    output = dup.dumps()
    import json

    header = json.loads(output.split("\n")[0])
    assert header["version"] == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_v3_duplicate.py -v`
Expected: FAIL — `duplicate()` doesn't copy `format_version`

- [ ] **Step 3: Update duplicate method**

In `src/asciinema_scene/scenelib/scene_content.py`, update `duplicate`:

```python
def duplicate(self) -> SceneContent:
    duplicate = SceneContent()
    duplicate.header = deepcopy(self.header)
    duplicate.frames = [line.copy() for line in self.frames]
    duplicate.format_version = self.format_version
    return duplicate
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_v3_duplicate.py -v`
Expected: All PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add src/asciinema_scene/scenelib/scene_content.py tests/test_v3_duplicate.py
git commit -m "fix: propagate format_version in duplicate()"
```

---

### Task 10: Final Integration and Regression Testing

**Files:**
- No new files (validation task)

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: All PASS

- [ ] **Step 2: Run linting**

Run: `uv run ruff check src`
Expected: No errors

- [ ] **Step 3: Run type checking**

Run: `uv run mypy`
Expected: No errors

- [ ] **Step 4: Run deptry**

Run: `uv run deptry src`
Expected: No issues

- [ ] **Step 5: Manual smoke test**

```bash
# Convert short.cast to v3
uv run sciine convert --format v3 -i tests/files/short.cast -o /tmp/short_v3.cast

# Verify it looks right
head -3 /tmp/short_v3.cast

# Apply an operation to v3 file
uv run sciine speed 2.0 -i /tmp/short_v3.cast | uv run sciine status

# Convert back to v2
uv run sciine convert --format v2 -i /tmp/short_v3.cast -o /tmp/short_v2_roundtrip.cast

# Compare with original
uv run sciine status -i tests/files/short.cast
uv run sciine status -i /tmp/short_v2_roundtrip.cast
```

- [ ] **Step 6: Commit any final fixes if needed**

If smoke testing reveals issues, fix them and commit.
