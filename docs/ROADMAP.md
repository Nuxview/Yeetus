# Yeetus — Project Roadmap

> Open source reimplementation of `docker init`, with multi-service support, auto stack detection, and configurable boilerplate levels.

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Done |
| 🔄 | In Progress |
| ⬜ | Not Started |

---

## Phase 0 — Project Setup ✅

- [x] `pyproject.toml` with all dependencies (typer, rich, jinja2, pydantic/dataclasses)
- [x] Basic package structure scaffolded (`yeetus/`, `tests/`)
- [x] `pytest` + `pytest-xdist` configured

---

## Phase 1 — Test Infrastructure (TDD First) ✅

> All tests must be written and failing before any implementation begins.

### Fixtures — Dummy Repos
- [x] `tests/fixtures/python-flask/`
- [x] `tests/fixtures/python-fastapi/`
- [x] `tests/fixtures/python-django/`
- [x] `tests/fixtures/node-nextjs/`
- [x] `tests/fixtures/node-react/`
- [x] `tests/fixtures/node-vite/`
- [x] `tests/fixtures/node-vue/`
- [x] `tests/fixtures/static-html/`

### Expected Output Snapshots
- [x] `tests/expected/python-flask-minimal/`
- [x] `tests/expected/python-flask-full/`
- [x] `tests/expected/python-fastapi-minimal/`
- [x] `tests/expected/python-fastapi-full/`
- [x] `tests/expected/python-django-minimal/`
- [x] `tests/expected/python-django-full/`
- [x] `tests/expected/node-nextjs-minimal/`
- [x] `tests/expected/node-nextjs-full/`
- [x] `tests/expected/node-react-minimal/`
- [x] `tests/expected/node-react-full/`
- [x] `tests/expected/node-vite-minimal/`
- [x] `tests/expected/node-vite-full/`
- [x] `tests/expected/node-vue-minimal/`
- [x] `tests/expected/node-vue-full/`
- [x] `tests/expected/static-html-minimal/`
- [x] `tests/expected/static-html-full/`

### Test Suite
- [x] `tests/conftest.py` — shared fixtures, tmp dir setup
- [x] `tests/test_generation.py` — parametrized across all 16 combos
  - [x] Files exist and are non-empty
  - [x] Content matches snapshots
  - [x] `docker compose config` passes
  - [x] `docker build` passes

---

## Phase 2 — Core Implementation ✅

> Implement until all 16 tests pass.

### Data Models (`models.py`)
- [x] `StackInfo` dataclass
- [x] `ProjectPart` dataclass
- [x] `ComposeConfig` dataclass

### Detectors (`detector/`)
- [x] `base.py` — shared `detect(path) -> StackInfo | None` interface
- [x] `python.py` — detects Flask / FastAPI / Django via `requirements.txt`, `pyproject.toml`, `uv.lock`
- [x] `node.py` — detects Next.js / React / Vite / Vue via `package.json` dependency inspection
- [x] `static.py` — detects static HTML via `index.html` with no `package.json`

### Templates (`templates/`)

**Python**
- [x] `python/Dockerfile.minimal.j2`
- [x] `python/Dockerfile.full.j2` (non-root user, HEALTHCHECK, layer caching, .env.example)

**Node**
- [x] `node/Dockerfile.minimal.j2`
- [x] `node/Dockerfile.full.j2`

**Static HTML**
- [x] `static/Dockerfile.minimal.j2`
- [x] `static/Dockerfile.full.j2`

**Compose**
- [x] `compose/compose.yaml.j2`

### Generator & Compose Builder
- [x] `generator.py` — renders Jinja2 templates to files
- [x] `compose_builder.py` — builds unified `ComposeConfig` from all `ProjectPart`s, handles:
  - [x] Inter-service `depends_on`
  - [x] Shared networks and volumes
  - [x] Cross-service env var references
  - [x] Port collision detection

### CLI (`cli.py`)
- [x] `init` command entry point
- [x] Prompts for project parts (name, path)
- [x] Runs detectors and presents results for confirmation/override
- [x] Prompts for boilerplate level (minimal / full)
- [x] Calls generator and compose builder
- [x] Outputs summary of generated files

---

## Phase 3 — Multi-Project Support ✅

- [x] Accept multiple project parts in a single `yeetus init` run
- [x] Generate a Dockerfile per part in its respective subdirectory
- [x] Wire all parts into one unified `compose.yaml`

---

## Phase 4 — Polish ✅

- [x] `--dry-run` flag (preview output without writing files)
- [x] `--no-detection` flag (skip auto-detection, prompt for everything)
- [x] Conflict handling (warn if Dockerfile already exists)
- [x] README generation per part
- [x] Proper CLI help text and `--version`

---

## Decisions Already Made

| Decision | Choice |
|----------|--------|
| Language | Python |
| CLI framework | Typer |
| Terminal output | Rich |
| Templating | Jinja2 |
| Data models | Dataclasses or Pydantic |
| Test runner | pytest + pytest-xdist |
| Go support | Dropped from Phase 1 |
| Development approach | TDD — tests before implementation |
