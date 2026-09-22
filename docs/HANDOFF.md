# Yeetus — Agent Handoff Prompt

## Context

We are building **Yeetus**, an open source Python CLI tool that recreates and extends the `docker init` command from Docker Desktop. The goal is to make this available without needing Docker Desktop installed — targeting users running standalone Docker Engine on Linux (e.g. CachyOS/Arch-based systems).

## What We're Building

A Python CLI scaffolding tool that generates Dockerfiles and a single unified `docker-compose.yaml` for multi-service projects. It is inspired by `docker init` but goes further.

---

## Features

### 1. Multi-Project Dockerfile Creation
The user specifies multiple parts of their project (e.g. frontend, backend, worker). For each part they declare:
- A name
- A path (subdirectory)
- The tech stack (auto-detected or manually specified)
- A boilerplate level (minimal or full)

Each part gets its own `Dockerfile` generated in its respective directory.

### 2. Full Docker Compose Wiring
Rather than generating separate compose files and merging them later, the tool builds a single in-memory `ComposeConfig` object as it processes each part, then renders one unified `compose.yaml` at the end. This allows proper handling of:
- Inter-service `depends_on`
- Shared networks and volumes
- Cross-service env var references
- Port collision detection

### 3. Auto Tech Stack Detection
Each tech stack has a detector module that traverses the project directory and identifies the stack from marker files:
- **Python**: `requirements.txt`, `pyproject.toml`, `uv.lock`
- **Node**: `package.json` + lockfile, then inspects dependencies for framework (`next`, `react`, `vite`, `vue`, etc.)
- **Static HTML**: presence of `index.html` with no package.json
- More stacks can be added via the shared detector interface

Detection results are presented to the user for confirmation/override before generation.

### 4. Boilerplate Levels
Two levels per stack:
- **Minimal**: Just enough to run the app (base image, copy files, install deps, entrypoint)
- **Full**: Adds non-root user + permissions, `HEALTHCHECK`, proper layer caching (deps installed before code copy), `.env.example` generation

---

## Supported Stacks (Phase 1)

| Stack         | Framework Detection |
|---------------|---------------------|
| Python        | Flask, FastAPI, Django |
| Node          | Next.js, React, Vite, Vue |
| Static HTML   | index.html (no package.json) |

---

## Planned Project Structure

```
yeetus/
├── cli.py                    # Entry point, orchestrates the full flow
├── models.py                 # Dataclasses: ProjectPart, StackInfo, ComposeConfig
├── generator.py              # Renders Jinja2 templates -> files
├── compose_builder.py        # Builds unified ComposeConfig from all ProjectParts
├── detector/
│   ├── __init__.py
│   ├── base.py               # Shared interface: detect(path) -> StackInfo | None
│   ├── python.py             # Detects Flask / FastAPI / Django
│   ├── node.py               # Detects Next.js / React / Vite / Vue
│   └── static.py             # Detects static HTML
├── templates/
│   ├── python/
│   │   ├── Dockerfile.minimal.j2
│   │   └── Dockerfile.full.j2
│   ├── node/
│   │   ├── Dockerfile.minimal.j2
│   │   └── Dockerfile.full.j2
│   ├── static/
│   │   ├── Dockerfile.minimal.j2
│   │   └── Dockerfile.full.j2
│   └── compose/
│       └── compose.yaml.j2
└── tests/
    ├── fixtures/             # Minimal dummy repos per stack
    │   ├── python-flask/
    │   ├── python-fastapi/
    │   ├── python-django/
    │   ├── node-nextjs/
    │   ├── node-react/
    │   ├── node-vite/
    │   ├── node-vue/
    │   └── static-html/
    ├── expected/             # Snapshot outputs per stack+level
    │   ├── python-flask-minimal/
    │   ├── python-flask-full/
    │   └── ... (16 total)
    ├── conftest.py
    └── test_generation.py    # Parametrized pytest suite
```

---

## Tech Stack

- **Language**: Python
- **CLI framework**: `typer` (preferred) or `click`
- **Terminal output**: `rich` (prompts, tables, progress)
- **Templating**: `Jinja2`
- **Data models**: Python `dataclasses` or `pydantic`
- **Testing**: `pytest` with `pytest-xdist` for parallel execution

---

## Development Approach: Test-Driven Development (TDD)

**Critical**: Implementation follows tests, not the other way around. Do not write implementation code before the corresponding tests and expected snapshots exist.

### TDD Build Order

1. **Define the test matrix** — all 16 stack/level combos (8 stacks × 2 boilerplate levels)
2. **Write fixture dummy repos** — minimal marker files per stack that trigger correct detection
3. **Design expected output snapshots** — what each Dockerfile and compose.yaml should look like per combo; this is where template design decisions are made
4. **Write the failing pytest suite** — parametrized tests that run generation and assert against snapshots
5. **Write the implementation** — detectors, templates, generator, compose builder — until all tests pass

### Test Matrix (16 cases)

| Stack | Minimal | Full |
|-------|---------|------|
| python-flask | ✓ | ✓ |
| python-fastapi | ✓ | ✓ |
| python-django | ✓ | ✓ |
| node-nextjs | ✓ | ✓ |
| node-react | ✓ | ✓ |
| node-vite | ✓ | ✓ |
| node-vue | ✓ | ✓ |
| static-html | ✓ | ✓ |

### Verification Order Per Test Case (fail fast)

1. **Files exist and are non-empty** — catches template rendering failures immediately
2. **Content matches snapshots** — catches regressions before spinning up Docker
3. **`docker compose config`** — validates compose YAML without building images
4. **`docker build`** — most expensive; only runs if all above pass

### Parametrized Test Structure

```python
@pytest.mark.parametrize("stack,level", [
    ("python-flask", "minimal"),
    ("python-flask", "full"),
    ("python-fastapi", "minimal"),
    # ... all 16 combos
])
def test_generation(stack, level, tmp_path):
    # 1. Copy fixture into tmp_path
    # 2. Run yeetus against it
    # 3. Assert files exist and are non-empty
    # 4. Assert content matches expected/ snapshot
    # 5. Run `docker compose config` and assert exit 0
    # 6. Run `docker build` and assert exit 0
```

---

## What To Do Next

Follow the TDD build order strictly:

1. **Set up the project** — `pyproject.toml`, dependencies, basic package structure
2. **Create all 8 fixture dummy repos** under `tests/fixtures/` with only the marker files needed for detection (no real app logic)
3. **Design and write all 16 expected output snapshots** under `tests/expected/` — this forces template design decisions to be made explicitly before any implementation
4. **Write `tests/test_generation.py`** — the full parametrized suite with all 4 verification steps; all tests should fail at this point
5. **Implement detectors, templates, generator, and compose builder** until all 16 tests pass

Keep the code clean, typed, and modular so additional stacks and features can be added easily in later phases.
