# Design: Timecode Colon-Format Support for --start / --end

**Date:** 2026-05-06

## Summary

Add `H:M:S` and `M:S` colon-notation support to the `--start` (`-s`) and `--end` (`-e`) options across all `sciine` commands, while keeping plain float (seconds) input working unchanged.

## Approach

Implement a custom `click.ParamType` subclass (`TimecodeParamType`) in `sciine.py`. It parses the user-supplied string and returns a `float` (seconds), so all downstream code (`scene.py`, etc.) remains unchanged.

## Accepted Formats

| Input | Interpretation | Result (float) |
|---|---|---|
| `90` | seconds | 90.0 |
| `90.5` | seconds with decimal | 90.5 |
| `1:30` | M:S | 90.0 |
| `1:30.5` | M:S with decimal seconds | 90.5 |
| `1:30:25` | H:M:S | 5425.0 |
| `1:30:25.5` | H:M:S with decimal seconds | 5425.5 |

## Conversion Logic

```
parts = value.split(":")
if 1 part:  float(parts[0])
if 2 parts: float(parts[0]) * 60 + float(parts[1])
if 3 parts: float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
else:       raise click.BadParameter
```

Validation rules:
- Minutes component (in `M:S` or `H:M:S`) must be in `[0, 59]`.
- Seconds component must be in `[0, 60)` (allowing 59.999... but not 60+).
- Any non-numeric part raises `click.BadParameter` with a helpful message.

## Code Changes

### `src/asciinema_scene/sciine.py`

1. Add `TimecodeParamType(click.ParamType)` class with `name = "timecode"` and a `convert` method.
2. Instantiate `TIMECODE = TimecodeParamType()`.
3. Change `start_option` and `end_option` from `type=float` to `type=TIMECODE`.
4. Update help strings:
   - `"Start timecode (seconds or [H:]M:S), default is 0.0."`
   - `"End timecode (seconds or [H:]M:S), default is EOF."`

No changes to `scene.py`, `scene_content.py`, `frame.py`, or any other file.

## Tests

New file `tests/test_timecode.py` (unit tests for `TimecodeParamType.convert` directly, plus CLI integration via `CliRunner`).

### Unit test cases

- Plain integer string `"90"` → `90.0`
- Plain float string `"90.5"` → `90.5`
- `"1:30"` → `90.0`
- `"1:30.5"` → `90.5`
- `"1:30:25"` → `5425.0`
- `"1:30:25.5"` → `5425.5`
- `"0:0"` → `0.0`
- `"0:0:0"` → `0.0`
- Invalid: `"1:60"` → `BadParameter` (seconds out of range)
- Invalid: `"1:60:00"` → `BadParameter` (minutes out of range)
- Invalid: `"abc"` → `BadParameter` (not a number)
- Invalid: `"1:2:3:4"` → `BadParameter` (too many parts)

### Integration test cases

- Invoke `cut` command via `CliRunner` with `--start 1:30 --end 2:00`, verify it produces correct output (no error, frames in expected range).
