# Repository Guidelines

## Project Structure & Module Organization

Yeetus is a Python 3.10+ CLI for scaffolding Docker configurations. Source lives in `yeetus/`: `cli.py` handles interaction, `models.py` defines dataclasses, `detector/` identifies stacks, `compose_builder.py` validates service configuration, and `generator.py` renders outputs. Jinja2 assets live in `yeetus/templates/`, grouped by stack and boilerplate level.

`tests/fixtures/` contains example projects; `tests/expected/` stores generated-file snapshots. Architecture, roadmap, and maintenance notes live in `docs/`. GitHub Actions workflows live in `.github/workflows/`.

## Build, Test, and Development Commands

- `uv sync --all-extras`: install project and development dependencies.
- `uv run yeetus init ./example --level minimal --dry-run`: preview scaffolding without writing files.
- `uv build`: build wheel and source distributions.
- `SKIP_DOCKER_BUILD=1 uv run pytest`: run CLI, regression, snapshot, and Compose checks without image builds.
- `uv run pytest -n 2`: run the complete suite, including image builds, HTTP startup checks, and healthchecks.
- `uv run ruff check .`: check lint rules.
- `uv run ruff format --check .`: verify formatting; use `uv run ruff format .` to apply it.

The fast suite requires Docker CLI and Compose. Container checks additionally require daemon access and network access for dependency downloads.

## Coding Style & Naming Conventions

Use four-space Python indentation and Ruff formatting. Use `snake_case` for modules, functions, and variables; `PascalCase` for classes; and `UPPER_SNAKE_CASE` for constants. Preserve type annotations and Python 3.10 compatibility. Keep prompts in the CLI, detection in detectors, and Docker instructions in templates named `Dockerfile.minimal.j2` or `Dockerfile.full.j2`.

## Testing Guidelines

Use pytest and pytest-xdist. Name files `test_*.py` and functions `test_*`. Write failing regression tests before fixes. For template changes, review snapshots and validate runnable containers at both levels. New stacks need registered detectors, templates, runnable fixtures, and snapshot/runtime coverage. No numeric coverage threshold is configured. CI checks Python 3.10–3.13 and Docker containers separately.

## Commit & Pull Request Guidelines

Follow existing imperative commit subjects, such as `Fix Docker scaffolding` or `Add support for custom entrypoints`. Describe the problem, resulting behavior, relevant issues, and validation in PRs. Keep changes focused and explain snapshot updates.

Update `README.md` and relevant `docs/` files when behavior changes. Do not edit `CHANGELOG.md`; GitHub Actions maintains it. Preserve custom ignore rules and keep secrets and local dependencies outside generated build contexts.
