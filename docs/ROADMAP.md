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

## Phase 0 — Project Setup ⬜

- [ ] `pyproject.toml` with all dependencies (typer, rich, jinja2, pydantic/dataclasses)
- [ ] Basic package structure scaffolded (`yeetus/`, `tests/`)
- [ ] `pytest` + `pytest-xdist` configured

---

## Phase 1 — Test Infrastructure (TDD First) ⬜

> All tests must be written and failing before any implementation begins.

### Fixtures — Dummy Repos
- [ ] `tests/fixtures/python-flask/`
- [ ] `tests/fixtures/python-fastapi/`
- [ ] `tests/fixtures/python-django/`
- [ ] `tests/fixtures/node-nextjs/`
- [ ] `tests/fixtures/node-react/`
- [ ] `tests/fixtures/node-vite/`
- [ ] `tests/fixtures/node-vue/`
- [ ] `tests/fixtures/static-html/`

### Expected Output Snapshots
- [ ] `tests/expected/python-flask-minimal/`
- [ ] `tests/expected/python-flask-full/`
- [ ] `tests/expected/python-fastapi-minimal/`
- [ ] `tests/expected/python-fastapi-full/`
- [ ] `tests/expected/python-django-minimal/`
- [ ] `tests/expected/python-django-full/`
- [ ] `tests/expected/node-nextjs-minimal/`
- [ ] `tests/expected/node-nextjs-full/`
- [ ] `tests/expected/node-react-minimal/`
- [ ] `tests/expected/node-react-full/`
- [ ] `tests/expected/node-vite-minimal/`
- [ ] `tests/expected/node-vite-full/`
- [ ] `tests/expected/node-vue-minimal/`
- [ ] `tests/expected/node-vue-full/`
- [ ] `tests/expected/static-html-minimal/`
- [ ] `tests/expected/static-html-full/`

### Test Suite
- [ ] `tests/conftest.py` — shared fixtures, tmp dir setup
- [ ] `tests/test_generation.py` — parametrized across all 16 combos
  - [ ] Files exist and are non-empty
  - [ ] Content matches snapshots
  - [ ] `docker compose config` passes
  - [ ] `docker build` passes

---

## Phase 2 — Core Implementation ⬜

> Implement until all 16 tests pass.

### Data Models (`models.py`)
- [ ] `StackInfo` dataclass
- [ ] `ProjectPart` dataclass
- [ ] `ComposeConfig` dataclass

### Detectors (`detector/`)
- [ ] `base.py` — shared `detect(path) -> StackInfo | None` interface
- [ ] `python.py` — detects Flask / FastAPI / Django via `requirements.txt`, `pyproject.toml`, `uv.lock`
- [ ] `node.py` — detects Next.js / React / Vite / Vue via `package.json` dependency inspection
- [ ] `static.py` — detects static HTML via `index.html` with no `package.json`

### Templates (`templates/`)

**Python**
- [ ] `python/Dockerfile.minimal.j2`
- [ ] `python/Dockerfile.full.j2` (non-root user, HEALTHCHECK, layer caching, .env.example)

**Node**
- [ ] `node/Dockerfile.minimal.j2`
- [ ] `node/Dockerfile.full.j2`

**Static HTML**
- [ ] `static/Dockerfile.minimal.j2`
- [ ] `static/Dockerfile.full.j2`

**Compose**
- [ ] `compose/compose.yaml.j2`

### Generator & Compose Builder
- [ ] `generator.py` — renders Jinja2 templates to files
- [ ] `compose_builder.py` — builds unified `ComposeConfig` from all `ProjectPart`s, handles:
  - [ ] Inter-service `depends_on`
  - [ ] Shared networks and volumes
  - [ ] Cross-service env var references
  - [ ] Port collision detection

### CLI (`cli.py`)
- [ ] `init` command entry point
- [ ] Prompts for project parts (name, path)
- [ ] Runs detectors and presents results for confirmation/override
- [ ] Prompts for boilerplate level (minimal / full)
- [ ] Calls generator and compose builder
- [ ] Outputs summary of generated files

---

## Phase 3 — Multi-Project Support ⬜

- [ ] Accept multiple project parts in a single `yeetus init` run
- [ ] Generate a Dockerfile per part in its respective subdirectory
- [ ] Wire all parts into one unified `compose.yaml`

---

## Phase 4 — Polish ⬜

- [ ] `--dry-run` flag (preview output without writing files)
- [ ] `--no-detection` flag (skip auto-detection, prompt for everything)
- [ ] Conflict handling (warn if Dockerfile already exists)
- [ ] README generation per part
- [ ] Proper CLI help text and `--version`

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
