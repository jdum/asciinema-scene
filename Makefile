.PHONY: install
install:
	uv sync

.PHONY: check
check: ## Run code quality tools.
	uv run tox -e lint
	uv run deptry src

.PHONY: lint
lint:
	uvx ruff check src

.PHONY: test
test: ## Test the code with pytest
	uv run pytest --cov-report=xml

.DEFAULT_GOAL := help
