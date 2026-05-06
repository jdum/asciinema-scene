# asciicast v3 Format Support

**Date:** 2026-05-06
**Status:** Approved

## Summary

Add full bidirectional support for the asciicast v3 file format to sciine. This includes reading v3 files, writing v3 files, preserving input format on output by default, an explicit `convert` command for v2↔v3 conversion, and first-class handling of all v3 event types (`o`, `i`, `m`, `r`, `x`).

## Format Differences (v2 vs v3)

| Aspect | v2 | v3 |
|--------|----|----|
| Time semantics | Absolute (seconds since start) | Relative (interval since previous event) |
| Terminal size | `width`/`height` top-level | `term.cols`/`term.rows` |
| Terminal type | `env.TERM` | `term.type` |
| Theme | Top-level `theme` object | `term.theme` |
| New header fields | — | `term.version`, `tags` |
| Comments | Not supported | Lines starting with `#` ignored |
| New event type | — | `x` (exit status) |
| Version field | `2` | `3` |

## Architecture

**Single internal model with format metadata.** The existing absolute-timecode representation (int microseconds) is retained. Format-version-aware parsing and serialization handle the conversion between relative intervals (v3) and absolute timecodes (internal).

### Rationale

- All existing operations (cut, speed, quantize, etc.) work on absolute timecodes. No changes needed to operation logic.
- Integer microsecond storage avoids floating-point drift during manipulation.
- v3's relative intervals are derived trivially from absolute timecodes on output.

## Detailed Design

### 1. Parsing (`SceneContent`)

**Format detection:** JSON-decode the first non-comment line. Check `header["version"]` → store as `self.format_version: int` (2 or 3).

**v3 parsing:**
- Skip lines starting with `#` (comments are discarded, not preserved)
- Header: extract `term.cols` → width, `term.rows` → height; store full original header dict for fields like `tags`, `term.version`, `term.theme`
- Events: convert relative intervals to absolute timecodes via cumulative sum:
  - `timecode[0] = interval[0]`
  - `timecode[n] = timecode[n-1] + interval[n]`
- All event types (`o`, `i`, `m`, `r`, `x`) become `Frame` objects

**v2 parsing:** Unchanged.

### 2. Serialization (`SceneContent.dumps()`)

Dispatch based on `self.format_version` (overridable by explicit format choice):

**v3 output:**
- Header: map internal fields to v3 schema (`term.cols`, `term.rows`, `term.type`, `term.theme`, etc.)
- Events: convert absolute timecodes to relative intervals (deltas):
  - `interval[0] = timecode[0]`
  - `interval[n] = timecode[n] - timecode[n-1]`
- Round intervals to 3 decimal places (millisecond precision per spec recommendation)
- Use error diffusion (Bresenham's) to avoid cumulative drift when rounding

**v2 output:** Unchanged.

### 3. Header Translation

```
v2 → v3:
  width        → term.cols
  height       → term.rows
  env.TERM     → term.type (if present)
  theme        → term.theme
  timestamp    → timestamp
  idle_time_limit → idle_time_limit
  command      → command
  title        → title
  env          → env (TERM removed if promoted to term.type)

v3 → v2:
  term.cols    → width
  term.rows    → height
  term.type    → env.TERM (merged into env)
  term.theme   → theme
  timestamp    → timestamp
  tags         → dropped (no v2 equivalent)
  term.version → dropped (no v2 equivalent)
```

### 4. Frame Model

No structural changes. The `Frame` class uses `tpe: str` and `text: str`, which accommodates all event types. Existing `match()`/`replace()` methods already guard on `tpe == "o"`, so `m`/`r`/`x` frames pass through all operations safely.

The `Frame.dumps()` method continues to serialize as a JSON array `[timecode_float, tpe, text]`. The conversion between absolute timecodes and relative intervals is handled at the `SceneContent.dumps()` level, not per-frame. `SceneContent.dumps()` computes deltas when outputting v3 format.

### 5. New CLI Command: `convert`

```
sciine convert --format v2|v3 [--input FILE] [--output FILE]
```

Reads input (any format, auto-detected), outputs in specified format. Pure format conversion with no frame manipulation.

### 6. Output Format Option

Add `--format` option to all write-producing commands. Values: `v2`, `v3`, or `auto` (default). `auto` preserves the input format version.

Implementation: a shared Click option decorator applied to all commands that produce output.

### 7. Comment Handling

v3 comments (lines starting with `#`) are discarded on parse. They are not preserved through transformations since frame positions change during operations like cut/speed/quantize.

### 8. Error Handling

- Missing/unknown `version` field in header → clear error message
- Negative intervals in v3 input → warning, treat as zero
- Invalid JSON lines → error with line number

### 9. Testing Strategy

- New v3 sample `.cast` files in `tests/files/`
- v3 parse + serialize round-trip tests
- All existing commands tested with v3 input (same operations, same results)
- `convert` command tests (v2→v3, v3→v2)
- Header translation tests (field mapping both directions)
- Regression: all existing v2 tests must continue to pass unchanged
- Edge cases: empty recordings, single-frame, large intervals, all event types

## Out of Scope

- Preserving v3 comments through transformations
- The `term.version` header field as a functional feature (stored, passed through, not used)
- Any new commands specific to v3 event types (e.g. marker manipulation) — future work
