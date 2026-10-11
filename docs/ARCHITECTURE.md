# Yeetus — Architecture & System Design

> This document details the architectural principles, data flow, subsystem components, template engine, and verification pipeline of Yeetus.

---

## 1. Design Philosophy

Yeetus was engineered around several foundational principles:

1. **Standalone Engine First**: Freedom from proprietary Docker Desktop dependencies, tailored specifically for developers running vanilla Docker Engine on Linux.
2. **Unified Compose Pipeline (No Post-Merge Hacks)**: Instead of generating individual `docker-compose.yaml` fragments and attempting to merge text/YAML post-hoc, Yeetus constructs a single, strongly-typed `ComposeConfig` model in memory. This eliminates merge anomalies and enables centralized validation (e.g. port collision detection and cross-service dependencies).
3. **Strict Separation of Concerns**:
   - **Detection** is decoupled from generation.
   - **Models** are purely declarative and framework-agnostic.
   - **Templates** contain container layout logic without CLI side-effects.
   - **CLI** manages user interaction and orchestration only.
4. **Test-Driven Rigor (TDD)**: Stack and level permutations use snapshot fixtures and verification through file checks, snapshot comparison, Compose validation, image builds, and container HTTP/health checks.

---

## 2. High-Level Architecture & Workflow

```mermaid
flowchart TD
    CLI["CLI Orchestrator (yeetus.cli)"]
    Detectors["Detector Engine (yeetus.detector)"]
    Models["Data Models (yeetus.models)"]
    ComposeBuilder["Compose Builder (yeetus.compose_builder)"]
    Generator["Template Generator (yeetus.generator)"]
    Disk["Filesystem (Dockerfile, .dockerignore, compose.yaml, .env.example)"]

    CLI -->|Scans target paths| Detectors
    Detectors -->|Returns StackInfo| CLI
    CLI -->|Prompts user & builds| Models
    Models -->|ProjectParts| Generator
    Generator -->|ProjectParts| ComposeBuilder
    ComposeBuilder -->|Validated ComposeConfig| Generator
    Generator -->|Renders Jinja2 templates| Disk
```

### Execution Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant CLI as CLI (yeetus.cli)
    participant Detector as Detectors (yeetus.detector)
    participant Builder as ComposeBuilder
    participant Gen as Generator (yeetus.generator)
    participant FS as Filesystem

    User->>CLI: yeetus init [path]
    CLI->>Detector: detect_stack(path)
    Detector-->>CLI: StackInfo (framework, port, cmd, package_manager, entrypoint)
    CLI->>User: Confirm stack & prompt for configuration (level, entrypoint, port)
    User-->>CLI: Confirmed configurations
    CLI->>Gen: generate(root_dir, parts, dry_run=True)
    Gen->>Builder: build([ProjectPart...])
    Note over Builder: Validates unique service names and ports; computes relative paths
    Builder-->>Gen: ComposeConfig
    Gen-->>CLI: Complete planned output list
    CLI->>FS: Check output conflicts, including README and ignore files
    CLI->>Gen: generate(root_dir, parts)
    Gen->>FS: Write Dockerfiles, ignore files, .env.examples, compose.yaml
    CLI->>User: Render Rich summary table & next steps
```

---

## 3. Subsystem Breakdown

### 3.1 Data Models (`yeetus.models`)

The core models provide the clean contract passed between detectors, builder, generator, and CLI:

- **`StackInfo`**: Represents detected runtime characteristics:
  - `stack_type`: High-level family (`python`, `node`, `static`).
  - `framework`: Specific framework (`flask`, `fastapi`, `django`, `nextjs`, `react`, `vite`, `vue`, `static`).
  - `port`: Default container port.
  - `cmd`: Execution command array/string.
  - `package_manager`: Package manager (`npm`, `pnpm`, `yarn`, `bun`).
  - `package_manager_version`: Validated semantic version from `packageManager`. pnpm installation uses this version, defaulting to major 9 when absent.
  - `entrypoint`: Primary entry file (e.g. `app.py`, `main.py`, `manage.py`).
  - `with_entrypoint(entrypoint)` & `with_package_manager(package_manager)`: Immutable transition helpers that reconfigure `cmd` and `.env.example`.
  - Flask commands include `--app` so minimal mode works without an environment file. FastAPI file paths become dotted import paths; absolute paths and parent traversal are rejected.
- **`ProjectPart`**: Represents a discrete service or subproject directory:
  - `name`: Service identifier (e.g. `web`, `api`, `frontend`).
  - `path`: Absolute filesystem path.
  - `stack_info`: Bound `StackInfo`.
  - `level`: Boilerplate level (`minimal` or `full`).
  - `depends_on`: Inter-service dependencies.
  - `port` / `target_port`: Port mappings.
- **`ComposeConfig` & `ComposeServiceConfig`**: Representation of the unified Docker Compose schema ready for Jinja2 rendering.

---

### 3.2 Detection Engine (`yeetus.detector`)

Detectors follow a shared interface (`BaseDetector`) and inspect marker files, dependency declarations, and project structures:

1. **Python Detector (`yeetus.detector.python`)**:
   - Markers inspected: `requirements.txt`, `pyproject.toml`, `uv.lock`, `Pipfile`, `setup.py`, `manage.py`.
   - Framework detection via regex matching on dependencies:
     - FastAPI: `fastapi`
     - Flask: `flask`
     - Django: `django` or presence of `manage.py`
     - Generic Python fallback
   - Entrypoint detection: Defaults to `main.py` (FastAPI), `manage.py` (Django), or `app.py` (Flask/Generic).
   - `detect_python_dependencies(path)` selects installation independently of the framework: locked uv project, requirements, pyproject with uv, Pipenv, setup.py with pip, or no installation for bare scripts. A uv lockfile without its project manifest is rejected during rendering.
2. **Node.js Detector (`yeetus.detector.node`)**:
   - Inspects `package.json` dependencies and devDependencies:
     - Next.js: `next`
     - Vite: `vite`
     - Vue: `vue`
     - React: `react`
     - Generic Node fallback
   - **Package Manager Detection (`detect_package_manager`)**:
     - Explicit declaration in `package.json`: `"packageManager": "pnpm@..."`
     - Configuration & lockfiles:
       - **bun**: `bun.lockb`, `bun.lock`, `bunfig.toml`
       - **pnpm**: `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `.pnpmfile.cjs`
       - **yarn**: `yarn.lock`, `.yarnrc.yml`, `.yarnrc`
       - **npm**: `package-lock.json`, `npm-shrinkwrap.json`, `.npmrc`
       - Default: `npm`
3. **Static HTML Detector (`yeetus.detector.static`)**:
   - Identifies static web applications by the presence of `index.html` without a `package.json`. Configures an Nginx Alpine container on port `80`.

---

### 3.3 Compose Builder (`yeetus.compose_builder`)

The `ComposeBuilder` translates a collection of `ProjectPart` instances into a unified `ComposeConfig`:
- **Context Normalization**: Calculates the build context relative to the root compose directory. If a part resides in a subdirectory `backend/`, its context is cleanly set to `backend`.
- **Port Collision Guard (`PortCollisionError`)**: Validates that no two services bind to the same host port. If a collision is detected (e.g. two services requesting port `8080`), an explicit `PortCollisionError` is raised before any files are written.
- **Service Names**: Rejects duplicate or invalid service names before rendering. Names follow Compose's letters/digits/underscore/dot/hyphen syntax and must start with a letter or digit.
- **Inter-Service Wiring**: Resolves `depends_on` relationships between services so that dependent services start in the proper order.
- **Environment File Association**: Automatically links `.env` configuration files for services configured with `full` boilerplate.

---

### 3.4 Template Generator (`yeetus.generator`)

The template system uses Jinja2 with `trim_blocks=True` and `lstrip_blocks=True`. The `yaml_string` filter serializes names, paths, and dependency names as JSON strings, which are valid quoted YAML scalars. This preserves paths containing comment markers, colons, and quotes.

Generation first builds the Compose model and renders every output into memory. Configuration and template errors are detected before any files are written. The CLI uses the same dry-run output list for conflict detection and previews, adding `README.docker.md` when enabled.

Each service receives `.dockerignore`. Existing content is preserved and the shared exclusions are appended; unchanged generated blocks remain idempotent. Existing `Dockerfile.dockerignore` files receive the same exclusions because Docker prioritizes them over the root ignore file. Exclusions cover environment secrets, repository metadata, local dependency directories, caches, and generated Docker scaffolding; `.env.example` remains available.

#### Template Directory Layout
```
yeetus/templates/
├── common/
│   └── dockerignore.j2
├── python/
│   ├── Dockerfile.minimal.j2
│   └── Dockerfile.full.j2
├── node/
│   ├── Dockerfile.minimal.j2
│   └── Dockerfile.full.j2
├── static/
│   ├── Dockerfile.minimal.j2
│   └── Dockerfile.full.j2
└── compose/
    └── compose.yaml.j2
```

#### Minimal vs. Full Boilerplate Matrix

| Feature | Minimal Level | Full Level |
|---|---|---|
| **Base Image** | Lightweight slim/alpine image | Lightweight slim/alpine image |
| **Dependencies** | Installed from the detected manifest | Requirements and Node dependencies use a separate layer; uv, Pipenv, and setup projects install after source copy |
| **Security** | Root user | Non-root unprivileged user (`appuser` / `node` / `nginx` / `bun`) |
| **Healthcheck** | None | Container `HEALTHCHECK` with zero-external-dependency curl/urllib/node/fetch probes |
| **Env Variables** | Base defaults | `.env.example` file generated with framework-specific keys |
| **Compose Restart**| None | `restart: unless-stopped` |

Python pyproject installations use uv at `/opt/venv`, with its executables on `PATH`; locked projects use `--locked`. Both Node levels install development dependencies and build Next.js before startup. Full Node images set `NODE_ENV=production` afterward and give the runtime user ownership of `/app`, including build caches. Full static images retain port 80 and place the Nginx PID in a writable `/run/nginx` directory, with a writable cache directory. Their healthcheck uses IPv4 loopback explicitly, since the non-root image entrypoint cannot rewrite the default configuration to enable IPv6.

---

### 3.5 CLI Layer (`yeetus.cli`)

Built with `typer` and `rich`:
- **Interactive Prompts**: Prompts for stack confirmation, boilerplate level, service names, and Python entrypoint files.
- **Non-Interactive Overrides**: Supports automated execution through flags (`--level`, `--entrypoint`, `--multi`, `--force`, `--dry-run`, `--no-detection`).
- **Conflict Handling**: Checks the complete planned output list, including `.dockerignore`, existing `Dockerfile.dockerignore`, and `README.docker.md`; prompts before writing unless `--force` is specified.
- **Dry-Run Mode**: Visualizes all files and types in a Rich preview table without performing filesystem modifications.

---

## 4. Verification & Testing Architecture

Yeetus uses a five-stage pipeline in `tests/test_generation.py`:

```mermaid
flowchart LR
    A["1. Non-empty file check"] --> B["2. Exact Snapshot Match"]
    B --> C["3. docker compose config"]
    C --> D["4. docker build"]
    D --> E["5. Container HTTP and health checks"]
```

1. **File Existence & Integrity**: Ensures all generated files exist and contain non-zero byte counts.
2. **Snapshot Comparison**: Asserts character-for-character equivalence against golden snapshots in `tests/expected/` across all 16 test matrix combinations.
3. **Compose Validation**: Executes `docker compose config` on the generated `compose.yaml` to ensure schema compliance.
4. **Live Image Compilation**: Invokes `docker build` on the scaffolded project to verify that package manager installations, dependency commands, and Dockerfile instructions compile without errors.
5. **Runtime Checks**: Starts the image with a dynamic localhost port, polls its HTTP endpoint and full-mode healthcheck, and removes the container in a `finally` block. Static cases also inspect image contents and verify secret paths return HTTP 404.

`tests/test_regressions.py` covers overwrite protection, Python entrypoints, dependency selection, duplicate services, literal YAML paths, and preservation/idempotency of ignore rules. Its offline npm probe verifies that full-mode installation includes development tools. `tests/test_container_regressions.py` builds additional Python dependency formats and alternative Node package managers. Next.js and Vite use real framework executables; React and Vue use small HTTP fixture scripts.

`SKIP_DOCKER_BUILD=1` disables build/start checks while retaining CLI, snapshot, regression, and Compose validation. Docker-enabled tests require daemon access and dependency download access. Containers are removed; images remain tagged `yeetus-test-*`.

CI runs the fast suite across Python 3.10–3.13 and the Docker generation/runtime suites separately on Python 3.12.

---

## 5. Adding New Tech Stacks

Yeetus is designed to be easily extensible. To introduce a new technology stack (e.g. Go, Rust, Ruby):

1. **Define Stack In Models (`yeetus/models.py`)**:
   Add new framework identifiers to `StackInfo`.
2. **Create Detector (`yeetus/detector/<stack>.py`)**:
   Implement `BaseDetector.detect(path: Path) -> StackInfo | None` searching for stack-specific markers (`go.mod`, `Cargo.toml`, `Gemfile`).
3. **Register Detector (`yeetus/detector/__init__.py`)**:
   Add the new detector to the `DETECTORS` list.
4. **Create Templates (`yeetus/templates/<stack>/`)**:
   Create `Dockerfile.minimal.j2` and `Dockerfile.full.j2`.
5. **Add Fixtures & Expected Snapshots**:
   Add dummy marker fixtures under `tests/fixtures/` and expected outputs under `tests/expected/`.
6. **Register in CLI Catalog (`yeetus/cli.py`)**:
   Add default framework entries to `FRAMEWORK_CATALOG`.
