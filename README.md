# Yeetus

![Last commit](https://img.shields.io/github/last-commit/Nuxview/Project-Tree)
![Repo size](https://img.shields.io/github/repo-size/Nuxview/Project-Tree)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-0B5FFF?logo=opensourceinitiative&logoColor=white)

> A FOSS, upgraded alternative to `docker init` that works without Docker Desktop.

`yeetus` scaffolds `Dockerfile`s and a unified `compose.yaml` for multi-service projects, targeting users running standalone Docker Engine.

---

## Features

- **Multi-service support** — configure any number of services in one run
- **Auto stack detection** — inspects your directories and identifies Python, Node, and more
- **Two boilerplate levels**:
  - `minimal` — bare-bones: base image, deps, copy, entrypoint
  - `full` — production-ready: non-root user, layer-cache optimisation, `HEALTHCHECK`, multi-stage builds for Node
- **Unified `compose.yaml`** — built in-memory across all parts, with port-collision detection
- **Extensible** — add new stacks by implementing the `BaseDetector` interface

### Detected stacks (Phase 1)

| Stack  | Marker files | Frameworks detected | Package managers |
|--------|-------------|---------------------|------------------|
| Python | `requirements.txt`, `pyproject.toml`, `setup.py`, `uv.lock`, `Pipfile` | fastapi, flask, django, starlette, litestar… | pip, uv, poetry |
| Node   | `package.json` | next, nuxt, remix, astro, express, fastify, vite… | npm, yarn, pnpm, bun |
| Static | `index.html`, `*.html` | — (served by nginx) | — |

---

## Installation

**With [uv](https://github.com/astral-sh/uv) (recommended):**

```bash
uv tool install yeetus
```

**From source:**

```bash
git clone https://github.com/Nuxview/Yeetus
cd yeetus
uv sync
uv run yeetus init
```

---

## Usage

```
yeetus init [OPTIONS]

Options:
  -p, --path PATH   Target project directory (default: current directory)
  --dry-run         Print what would be generated without writing files
  --help            Show this message and exit
```

**Run in the current directory:**
```bash
yeetus init
```

**Run for a project in a different directory:**
```bash
yeetus init --path /path/to/project
yeetus init -p /path/to/project
```

### Example session

```
$ yeetus init

╭─────────────────────────────────────────╮
│ yeetus  v0.1.0                         │
│ Scaffolding my-app  /home/user/my-app   │
╰─────────────────────────────────────────╯

How many services / parts does your project have? [1]: 2

──────────────── Service 1 of 2 ────────────────
  Name [service1]: backend
  Path (relative to project root) [./backend]:
  ✓ Detected: python v3.11 (fastapi) [uv]
  Confirm detected stack? [Y/n]:
  Port (blank to skip): 8000
  Boilerplate level (minimal/full) [minimal]:

──────────────── Service 2 of 2 ────────────────
  Name [service2]: frontend
  Path (relative to project root) [./frontend]:
  ✓ Detected: node v20 (next) [npm]
  Confirm detected stack? [Y/n]:
  Port (blank to skip): 3000
  Boilerplate level (minimal/full) [minimal]: full

┌─ Service Configuration ──────────────────────────┐
│ Name     Path       Stack              Level Port │
│ backend  ./backend  python v3.11 …     min   8000 │
│ frontend ./frontend node v20 (next)…   full  3000 │
└──────────────────────────────────────────────────┘

Generate files? [Y/n]:

──────────────── Generating ────────────────
  ✓ backend/Dockerfile
  ✓ frontend/Dockerfile
  ✓ compose.yaml

Done!  Build and start your project:

  docker compose up --build
```

---

## Project structure

```
yeetus/
├── pyproject.toml
└── yeetus/
    ├── cli.py              # Entry point — Typer app + interactive prompts
    ├── models.py           # Dataclasses: ProjectPart, StackInfo, ComposeConfig
    ├── generator.py        # Jinja2 template renderer → Dockerfile / compose.yaml
    ├── compose_builder.py  # Assembles unified ComposeConfig from all parts
    ├── detector/
    │   ├── base.py         # BaseDetector ABC
    │   ├── python.py       # Python detector
    │   ├── node.py         # Node detector
    │   └── static.py       # Static detector
    └── templates/
        ├── python/         # Dockerfile.minimal.j2  Dockerfile.full.j2
        ├── node/           # Dockerfile.minimal.j2  Dockerfile.full.j2
        ├── static/         # Dockerfile.minimal.j2  Dockerfile.full.j2
        └── compose/        # compose.yaml.j2
```

---

## License

[MIT](LICENSE)
