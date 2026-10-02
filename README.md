# Yeetus

> An open-source, upgraded alternative to Docker Desktop's proprietary `docker init` CLI tool, built for developers running standalone Docker Engine on Linux and multi-service architectures.

[![Tests](https://img.shields.io/badge/tests-44%20passed-brightgreen.svg)]()
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Python: >=3.11](https://img.shields.io/badge/python-%3E%3D3.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Why Yeetus?

Docker Desktop includes a handy `docker init` command that scaffolds Docker assets for your projects. However:
1. **Docker Desktop is not standalone Docker Engine**: Users running standalone Docker Engine on Linux distributions (such as Arch Linux, CachyOS, Debian, Ubuntu, Fedora) do not have access to `docker init` without running proprietary Docker Desktop.
2. **Single-Service Limitations**: Standard `docker init` focuses on single-service setups and doesn't gracefully coordinate multi-service projects or monorepos.
3. **Limited Tooling Awareness**: Many modern Node projects use alternative package managers like **pnpm**, **yarn**, or **bun**, and Python projects frequently employ custom entrypoints rather than default filenames.

**Yeetus** solves all of these problems with an extensible, open-source Python CLI designed for standalone Docker Engine.

---

## Key Features

- **Multi-Service Project Scaffolding**: Configure multiple services in a single run (e.g. frontend, API, worker) with distinct tech stacks, subdirectories, and inter-service dependencies (`depends_on`).
- **Unified Docker Compose Generation**: Builds a unified in-memory `ComposeConfig` that validates port collisions, resolves relative directory contexts, and renders a single, clean `compose.yaml`.
- **Intelligent Tech Stack & Framework Detection**:
  - **Python**: Detects Flask, FastAPI, Django, and generic Python from `requirements.txt`, `pyproject.toml`, `uv.lock`, and project markers.
  - **Node.js**: Detects Next.js, React, Vite, Vue, and generic Node by inspecting dependencies in `package.json`.
  - **Package Manager Detection**: Scans for `packageManager` declarations and lockfiles to configure **npm**, **pnpm**, **yarn**, or **bun**.
  - **Static Web**: Detects static sites and provisions optimized Nginx containers.
- **Python Entrypoint Prompting**: Identifies entrypoints like `app.py`, `manage.py`, or `main.py` and prompts the user, seamlessly configuring WSGI/ASGI commands (`uvicorn`, `flask run`, etc.) and environment variables.
- **Configurable Boilerplate Levels**:
  - `minimal`: Lightweight, fast development Dockerfiles (base image, dependencies, copy, port, entrypoint).
  - `full`: Production-grade containerization with non-root unprivileged users, file permissions, layer caching, `HEALTHCHECK` definitions, and `.env.example` templates.
- **Modern Interactive CLI**:
  - Interactive prompts powered by [Rich](https://github.com/Textualize/rich) and [Typer](https://github.com/tiangolo/typer).
  - Rich summary tables, dry-run previews, conflict warnings before overwriting, and automated documentation generation (`README.docker.md`).

---

## Supported Stacks & Matrix

| Stack | Frameworks | Package Managers | Levels |
|---|---|---|---|
| **Python** | Flask, FastAPI, Django, Generic | pip, uv | Minimal, Full |
| **Node.js** | Next.js, React, Vite, Vue, Generic | npm, pnpm, yarn, bun | Minimal, Full |
| **Static HTML** | Static Sites (Nginx) | N/A | Minimal, Full |

---

## Installation

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (Docker Engine 20.10+ / Compose v2+)

### Install from Source
Using [`uv`](https://github.com/astral-sh/uv) (recommended):
```bash
git clone https://github.com/Nuxview/yeetus.git
cd yeetus
uv tool install .
```

Or using standard `pip`:
```bash
pip install .
```

---

## Quick Start

### 1. Interactive Initialization
Run `yeetus init` in your project root:
```bash
yeetus init
```
Yeetus will automatically detect your tech stack, present its findings, prompt for configuration options (such as boilerplate level and entrypoint), and generate your Dockerfile and `compose.yaml`.

### 2. Multi-Service Projects
To configure multi-service monorepos:
```bash
yeetus init --multi
```
You can name each service, point to its subdirectory, configure inter-service `depends_on`, and wire everything into one cohesive `compose.yaml`.

### 3. Non-Interactive / Scriptable CLI
Yeetus provides flags for CI/CD and scripted environments:
```bash
# Full boilerplate for a FastAPI project with custom entrypoint
yeetus init ./backend --level full --entrypoint api_server.py --no-readme

# Preview files without writing to disk
yeetus init --dry-run

# Skip auto-detection and prompt manually
yeetus init --no-detection

# Overwrite existing files without prompting
yeetus init --force
```

### 4. Running Your Container
Once files are generated, launch your services:
```bash
docker compose up --build
```

---

## CLI Reference

```
Usage: yeetus init [OPTIONS] [PATH]

Arguments:
  [PATH]                      Target project directory (default: current directory)

Options:
  -l, --level TEXT            Boilerplate level: 'minimal' or 'full'
  --dry-run                   Preview generated files without writing to disk
  --no-detection              Skip auto-detection and prompt manually for tech stack
  -f, --force                 Overwrite existing files without prompting
  -m, --multi                 Configure a multi-service project
  -e, --entrypoint TEXT       Main Python entrypoint file (e.g. app.py, main.py)
  --readme / --no-readme      Generate README.docker.md documentation [default: True]
  --help                      Show help message and exit
```

---

## Development & Testing

Yeetus is built with Test-Driven Development (TDD). Every supported stack and level is validated against snapshot outputs and tested with `docker compose config` and `docker build`.

### Run Test Suite
```bash
# Sync dependencies
uv sync --all-extras

# Run all unit and snapshot tests (skipping container image build)
SKIP_DOCKER_BUILD=1 uv run pytest

# Run full test suite including live docker builds
uv run pytest
```

### Code Style & Quality
```bash
# Check code style with Ruff
uv run ruff check

# Verify formatting
uv run ruff format --check
```

---

## Documentation

For a detailed look into Yeetus' internal architecture, data models, template engine, and extensibility guide, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
