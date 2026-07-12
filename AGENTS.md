# AGENTS.md

## What This Is

Python CLI toolkit (`sciine`) for editing asciinema `.cast` recording files. Composable, pipe-friendly commands. Entry point: `src/asciinema_scene/sciine.py`.

## Setup

```bash
uv sync   # installs all deps; use uv exclusively — not pip or poetry
```

## Key Commands

```bash
uv run pytest                         # run all tests (no coverage)
uv run pytest --cov --cov-report=xml  # with coverage (or: make test)
uv run pytest tests/test_copy.py      # single file
uv run pytest -k "test_copy_start"    # single test by name
uv run ruff check src                 # lint (or: make lint) — ruff will NOT auto-fix (fix = false)
uv run mypy                           # typecheck — strict mode
uv run tox -e lint                    # lint + typecheck together
uv run deptry src                     # dependency audit
make check                            # tox lint + deptry
uv run sciine --help                  # run the CLI
```

## Toolchain Quirks

- **Build backend**: `uv_build` (not hatchling/setuptools). Version pinned `>=0.9.0,<0.10.0`.
- **Ruff**: `fix = false` — reports issues but never auto-applies fixes. Line length 88. `S101` (assert) allowed in tests.
- **Mypy is strict**: `disallow_untyped_defs`, `disallow_any_unimported`, `warn_return_any` all enabled. New code must be fully typed.
- **isort via ruff**: Import ordering enforced by ruff's `I` rule set, not standalone `isort`.
- **Pytest config**: In `pyproject.toml` under `[tool.pytest.ini_options]`, `testpaths = ["tests"]`.
- **CI branch**: Runs on pushes to `devel` (not `main`) and on PRs. Coverage uploaded only from Python 3.14 tox env.
- **Python range**: `>=3.10, <4.0`; tox matrix covers 3.10–3.14.

## Structure

```
src/asciinema_scene/
  sciine.py          # all Click CLI commands
  scenelib/
    scene.py         # high-level scene manipulation
    scene_content.py # .cast parsing/serialization
    frame.py         # Frame data model
tests/
  contents.py        # shared test fixtures/data
  files/             # sample .cast files
contrib/             # custom sample / helper scripts
  quantize_cast.sh   # example: asciicast v3 → v2 quantization
```

## Conventions

- Commands read from stdin, write to stdout by default — maintain this for new commands.
- Test data lives in `tests/contents.py` (inline) and `tests/files/` (sample files).
- Custom sample scripts live in `contrib/`.
- No separate format command; formatting issues surface through `ruff check`.
