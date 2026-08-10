## Makefile (repo-owned)
# Keep this file small. It can be edited without breaking template sync.

DEFAULT_AI_MODEL=claude-sonnet-4.6
LOGO_FILE=.rhiza/assets/rhiza-logo.svg
GH_AW_ENGINE ?= copilot  # Default AI engine for gh-aw workflows (copilot, claude, or codex)

# Override template default: include mkdocstrings plugin for API docs
MKDOCS_EXTRA_PACKAGES = --with 'mkdocstrings[python]'

# Always include the Rhiza API (template-managed)
include .rhiza/rhiza.mk

# Override template defaults with realistic thresholds for this project
# (Must come after include to override template variables)
COVERAGE_FAIL_UNDER ?= 85
DOCS_COVERAGE_THRESHOLD ?= 59

.PHONY: docs-coverage
docs-coverage: install
	@echo "Running docs coverage with threshold: $(DOCS_COVERAGE_THRESHOLD)%"
	@uv run --with interrogate interrogate -vv --fail-under $(DOCS_COVERAGE_THRESHOLD) --ignore-init-method --ignore-magic src/

# Override template default: use pyproject.toml config instead of --strict
.PHONY: typecheck
typecheck: install
	@echo "Running mypy type checking..."
	@uv run --with mypy mypy src/

# Project-specific CI target: runs all validation without rhiza-test
# (rhiza-test validates strict template conformance, which fails for custom configs)
.PHONY: ci
ci: fmt deps test docs-coverage security license typecheck ## run all project CI targets locally (excludes rhiza-test)

# Optional: developer-local extensions (not committed)
-include local.mk
