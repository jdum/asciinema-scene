.PHONY: install
install:
	uv sync

.PHONY: lock
lock:
	uv lock --upgrade

.PHONY: check
check: ## Run code quality tools.
	uv run tox -e lint
	uv run deptry src

.PHONY: lint
lint:
	uv run ruff check src

.PHONY: test
test: ## Test the code with pytest
	uv run pytest --cov --cov-report=xml

.DEFAULT_GOAL := help
