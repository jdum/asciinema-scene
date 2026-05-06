# Timecode Colon-Format Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow `--start` / `--end` options to accept `M:S` and `H:M:S` colon-notation (with optional decimal seconds) in addition to plain float seconds.

**Architecture:** Add a `TimecodeParamType(click.ParamType)` class in `sciine.py` that converts colon-format strings to `float` at parse time. Swap `type=float` → `type=TIMECODE` on `start_option` and `end_option`. All downstream scene code stays unchanged.

**Tech Stack:** Python 3.10+, Click 8.x, pytest, uv

---

### Task 1: Add `TimecodeParamType` with unit tests

**Files:**
- Create: `tests/test_timecode.py`
- Modify: `src/asciinema_scene/sciine.py`

- [ ] **Step 1: Write the failing unit tests**

Create `tests/test_timecode.py`:

```python
import pytest
from click.exceptions import BadParameter

from asciinema_scene.sciine import TimecodeParamType

TIMECODE = TimecodeParamType()


def convert(value: str) -> float:
    return TIMECODE.convert(value, param=None, ctx=None)  # type: ignore[arg-type]


def test_plain_integer():
    assert convert("90") == 90.0


def test_plain_float():
    assert convert("90.5") == 90.5


def test_minutes_seconds():
    assert convert("1:30") == 90.0


def test_minutes_seconds_decimal():
    assert convert("1:30.5") == 90.5


def test_hours_minutes_seconds():
    assert convert("1:30:25") == 5425.0


def test_hours_minutes_seconds_decimal():
    assert convert("1:30:25.5") == 5425.5


def test_zero_ms():
    assert convert("0:0") == 0.0


def test_zero_hms():
    assert convert("0:0:0") == 0.0


def test_seconds_out_of_range():
    with pytest.raises(BadParameter):
        convert("1:60")


def test_minutes_out_of_range():
    with pytest.raises(BadParameter):
        convert("1:60:00")


def test_non_numeric():
    with pytest.raises(BadParameter):
        convert("abc")


def test_too_many_parts():
    with pytest.raises(BadParameter):
        convert("1:2:3:4")


def test_negative_rejected():
    with pytest.raises(BadParameter):
        convert("1:-1")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_timecode.py -v
```

Expected: `ImportError` or `AttributeError` — `TimecodeParamType` not yet defined.

- [ ] **Step 3: Implement `TimecodeParamType` in `sciine.py`**

Add this class near the top of `src/asciinema_scene/sciine.py`, after the imports and before `input_option`:

```python
class TimecodeParamType(click.ParamType):
    name = "timecode"

    def convert(
        self,
        value: str | float,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> float:
        if isinstance(value, float):
            return value
        parts = str(value).split(":")
        if len(parts) == 1:
            try:
                return float(parts[0])
            except ValueError:
                self.fail(
                    f"{value!r} is not a valid timecode (use seconds or [H:]M:S)",
                    param,
                    ctx,
                )
        if len(parts) == 2:
            try:
                minutes = float(parts[0])
                seconds = float(parts[1])
            except ValueError:
                self.fail(
                    f"{value!r} is not a valid timecode (use seconds or [H:]M:S)",
                    param,
                    ctx,
                )
            if minutes < 0 or seconds < 0 or seconds >= 60:
                self.fail(
                    f"{value!r}: minutes must be >= 0 and seconds must be in [0, 60)",
                    param,
                    ctx,
                )
            return minutes * 60 + seconds
        if len(parts) == 3:
            try:
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
            except ValueError:
                self.fail(
                    f"{value!r} is not a valid timecode (use seconds or [H:]M:S)",
                    param,
                    ctx,
                )
            if hours < 0 or minutes < 0 or minutes >= 60 or seconds < 0 or seconds >= 60:
                self.fail(
                    f"{value!r}: hours >= 0, minutes in [0, 60), seconds in [0, 60)",
                    param,
                    ctx,
                )
            return hours * 3600 + minutes * 60 + seconds
        self.fail(
            f"{value!r} is not a valid timecode (use seconds or [H:]M:S)",
            param,
            ctx,
        )


TIMECODE = TimecodeParamType()
```

- [ ] **Step 4: Run unit tests to verify they pass**

```bash
uv run pytest tests/test_timecode.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_timecode.py src/asciinema_scene/sciine.py
git commit -m "feat: add TimecodeParamType for colon-format timecode parsing"
```

---

### Task 2: Wire `TIMECODE` into `start_option` and `end_option`

**Files:**
- Modify: `src/asciinema_scene/sciine.py` (lines ~27-38)

- [ ] **Step 1: Update `start_option` and `end_option`**

In `src/asciinema_scene/sciine.py`, replace:

```python
start_option = click.option(
    "--start",
    "-s",
    type=float,
    help="Start timecode (sec), default is 0.0.",
)
end_option = click.option(
    "--end",
    "-e",
    type=float,
    help="End timecode (sec), default is EOF.",
)
```

with:

```python
start_option = click.option(
    "--start",
    "-s",
    type=TIMECODE,
    help="Start timecode (seconds or [H:]M:S), default is 0.0.",
)
end_option = click.option(
    "--end",
    "-e",
    type=TIMECODE,
    help="End timecode (seconds or [H:]M:S), default is EOF.",
)
```

- [ ] **Step 2: Run the full test suite**

```bash
uv run pytest -v
```

Expected: all existing tests PASS (no regressions; `TIMECODE.convert` returns `float` so downstream is unchanged).

- [ ] **Step 3: Commit**

```bash
git add src/asciinema_scene/sciine.py
git commit -m "feat: wire TimecodeParamType into --start and --end options"
```

---

### Task 3: Integration tests via CliRunner

**Files:**
- Modify: `tests/test_timecode.py`

- [ ] **Step 1: Add integration tests**

Append to `tests/test_timecode.py`:

```python
from click.testing import CliRunner

from asciinema_scene.sciine import cli
from tests.contents import SHORT_FILE_CONTENT


def test_cut_with_colon_start():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["cut", "--start", "0:04"],
        input=SHORT_FILE_CONTENT,
    )
    assert result.exit_code == 0


def test_cut_with_colon_start_end():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["cut", "--start", "0:04", "--end", "0:10"],
        input=SHORT_FILE_CONTENT,
    )
    assert result.exit_code == 0


def test_cut_with_hms():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["cut", "--start", "0:0:4", "--end", "0:0:10"],
        input=SHORT_FILE_CONTENT,
    )
    assert result.exit_code == 0


def test_invalid_timecode_error():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["cut", "--start", "bad"],
        input=SHORT_FILE_CONTENT,
    )
    assert result.exit_code != 0
    assert "timecode" in result.output.lower() or "invalid" in result.output.lower()
```

- [ ] **Step 2: Run integration tests**

```bash
uv run pytest tests/test_timecode.py -v
```

Expected: all tests PASS.

- [ ] **Step 3: Run full suite and lint**

```bash
uv run pytest -v && uv run ruff check src && uv run mypy
```

Expected: all PASS, no lint or type errors.

- [ ] **Step 4: Commit**

```bash
git add tests/test_timecode.py
git commit -m "test: add integration tests for colon-format timecode in CLI options"
```
