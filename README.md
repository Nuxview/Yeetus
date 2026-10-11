# Yeetus

> An open-source, upgraded alternative to Docker Desktop's proprietary `docker init` CLI tool, built for developers running standalone Docker Engine on Linux and multi-service architectures.

[![Tests](https://github.com/Nuxview/Yeetus/actions/workflows/ci.yml/badge.svg)](https://github.com/Nuxview/Yeetus/actions/workflows/ci.yml)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Python: >=3.10](https://img.shields.io/badge/python-%3E%3D3.10-blue.svg)](https://www.python.org/)
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
- **Unified Docker Compose Generation**: Builds an in-memory `ComposeConfig` that validates unique service names and port collisions, quotes relative directory paths, and renders a single `compose.yaml`.
- **Intelligent Tech Stack & Framework Detection**:
  - **Python**: Detects Flask, FastAPI, Django, and generic Python; chooses installation from `requirements.txt`, `pyproject.toml`/`uv.lock`, `Pipfile`, or `setup.py`. Scripts without a dependency manifest skip installation.
  - **Node.js**: Detects Next.js, React, Vite, Vue, and generic Node by inspecting dependencies in `package.json`.
  - **Package Manager Detection**: Scans for `packageManager` declarations and lockfiles to configure **npm**, **pnpm**, **yarn**, or **bun**.
  - **Static Web**: Detects static sites and provisions optimized Nginx containers.
- **Python Entrypoint Prompting**: Configures custom Flask entrypoints in both levels and preserves nested FastAPI modules (for example, `src/api.py` becomes `src.api:app`).
- **Build Context Exclusions**: Generates `.dockerignore` rules for environment secrets, repository metadata, and local dependency directories. Preserves existing custom rules and appends the exclusions to an existing `Dockerfile.dockerignore` too.
- **Node Build Steps**: Installs development dependencies needed by Vite and Vue scripts and compiles Next.js before its production start command.
- **Configurable Boilerplate Levels**:
  - `minimal`: Lightweight, fast development Dockerfiles (base image, dependencies, copy, port, entrypoint).
  - `full`: Adds non-root users, writable application directories, dependency layer caching where applicable, `HEALTHCHECK` definitions, and `.env.example` templates. Static Nginx services use writable PID and cache directories.
- **Modern Interactive CLI**:
  - Interactive prompts powered by [Rich](https://github.com/Textualize/rich) and [Typer](https://github.com/tiangolo/typer).
  - Rich summary tables, dry-run previews, conflict warnings before overwriting, and automated documentation generation (`README.docker.md`).

---

## Supported Stacks & Matrix

| Stack | Frameworks | Package Managers | Levels |
|---|---|---|---|
| **Python** | Flask, FastAPI, Django, Generic | pip, uv, Pipenv | Minimal, Full |
| **Node.js** | Next.js, React, Vite, Vue, Generic | npm, pnpm, yarn, bun | Minimal, Full |
| **Static HTML** | Static Sites (Nginx) | N/A | Minimal, Full |

---

## Installation

### Prerequisites
- Python 3.10+ (for the Yeetus CLI; generated Python images default to 3.12)
- Docker & Docker Compose (Docker Engine 20.10+ / Compose v2.24+)

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
Yeetus detects your tech stack, presents its findings, prompts for configuration options, and generates `Dockerfile`, `.dockerignore`, `compose.yaml`, and `README.docker.md`. Full mode also generates `.env.example`. Existing output files, including the Docker README and ignore files, require overwrite confirmation unless `--force` is set.

### 2. Multi-Service Projects
To configure multi-service monorepos:
```bash
yeetus init --multi
```
Name each service, point to its subdirectory, configure `depends_on`, and choose its host port. Names must be unique and contain letters, digits, underscores, dots, or hyphens, starting with a letter or digit. Changing a host port preserves the framework's internal port, for example `8080:3000` for Next.js.

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

### 4. Dependency Installation and Entrypoints

Python installation follows this order:

| Project files | Generated installation |
|---|---|
| `pyproject.toml` and `uv.lock` | `uv sync --locked --no-dev --no-editable` |
| `requirements.txt` | `pip install -r requirements.txt` |
| `pyproject.toml` | `uv sync --no-dev --no-editable` |
| `Pipfile` | Pipenv system installation; uses deploy mode when `Pipfile.lock` exists |
| `setup.py` | `pip install .` |
| Python scripts only | No dependency installation |

An orphan `uv.lock` requires its `pyproject.toml`. The uv environment is created at `/opt/venv` and added to `PATH`. Project files must be available within the service's build context, including any local dependencies.

Flask receives `--app <entrypoint>` directly. FastAPI expects an `app` object and a file path relative to the service directory, such as `--entrypoint src/api.py`.

Next.js images run the local Next.js build executable before startup. Node images install development dependencies before setting full mode's `NODE_ENV=production`. pnpm uses the semantic version declared in `packageManager`, or pnpm 9 when no version is declared. Vite, React, and Vue keep their detected `dev`, `start`, or `serve` scripts; full mode adds container safeguards while retaining those application commands.

### 5. Running Your Container
Once files are generated, launch your services:
```bash
docker compose up --build
```

Full mode loads `.env` when present. Copy and customize `.env.example` if your application needs these variables. Generated ignore rules exclude `.env` and `.env.*` while allowing `.env.example`; they also exclude `.git`, `.aws`, `.ssh`, `.npmrc`, `.pypirc`, virtual environments, and `node_modules`. Custom ignore rules remain at the start of each file, followed by Yeetus' exclusions. Configure build secrets separately when dependency installation requires private registry credentials.

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

The suite checks CLI behavior, regression cases, snapshots, and `docker compose config`. Docker-enabled runs also build images, start containers on dynamically allocated localhost ports, check HTTP responses and full-mode healthchecks, and remove test containers. Static image checks verify that secret files and local dependencies are excluded. Additional containers cover Python dependency formats, custom entrypoints, and Node package managers.

### Run Test Suite
```bash
# Sync dependencies
uv sync --all-extras

# Run unit, regression, snapshot, and Compose checks without a Docker daemon
# (the Docker CLI and Compose plugin are still required)
SKIP_DOCKER_BUILD=1 uv run pytest

# Run the full suite, including image builds and container startup
# Requires Docker daemon access and network access for dependency downloads
uv run pytest -n 2
```

Test images remain tagged `yeetus-test-*` for inspection. Next.js and Vite fixtures exercise their actual build/server executables; React and Vue fixtures use small HTTP scripts to check package installation, script invocation, ports, and permissions.

GitHub Actions runs the fast suite on Python 3.10–3.13 and a separate Docker build/start job on Python 3.12.

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
