test:
    uv run pytest

ty:
    ty check src tests

ruff:
    ruff check src tests

deptry:
    uv run deptry src

lint: ruff ty deptry

cov:
    uv run pytest --cov --cov-report=xml

lock:
    uv lock -U

sync:
    uv sync

install: sync

code: lock sync lint test cov

check: sync lint test
