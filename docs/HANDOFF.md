# Yeetus — Agent Handoff

Yeetus is a Python 3.10+ CLI that scaffolds Dockerfiles, build exclusions, and a unified Compose file for single-service and multi-service projects.

## Current implementation

- `yeetus/cli.py` handles prompts, stack confirmation, levels, custom Python entrypoints, and host ports. It previews the real output list before checking conflicts, including `README.docker.md` and ignore files.
- `yeetus/models.py` defines stack, project-part, and Compose dataclasses. Flask receives an explicit `--app` argument; relative FastAPI file paths become dotted module paths.
- `yeetus/detector/` detects Python, Node, and static projects. Python dependency selection prefers a locked uv project, then requirements, pyproject with uv, Pipenv, setup.py, or no installation for bare scripts.
- `yeetus/compose_builder.py` validates unique service names and host-port collisions and computes relative build contexts. Custom host ports retain the original internal service port.
- `yeetus/generator.py` renders all outputs before writing them. Compose strings use quoted YAML scalars. Existing custom ignore rules are preserved, with shared exclusions appended to both `.dockerignore` and any existing `Dockerfile.dockerignore`.
- `yeetus/templates/` contains Python, Node, static, Compose, and shared ignore templates. Both levels build Next.js before startup. Node installation includes development dependencies, and full mode sets its runtime environment afterward.
- Full Node containers own their application and cache files. Full static containers retain port 80 and use writable Nginx PID and cache directories.
- pnpm installation honors a validated declared version and defaults to major 9; full mode copies workspace build-policy files before dependency installation. Static healthchecks use IPv4 loopback explicitly.

The CLI writes a Dockerfile and ignore file per service, `.env.example` for full services, and one `compose.yaml` and optional Docker README at the root. Existing output files require confirmation unless `--force` is set. `--dry-run` previews without writing.

Generated Python images default to Python 3.12. uv uses `/opt/venv` and its executables are placed on `PATH`. A uv lockfile requires its project manifest. Full mode adds container safeguards and healthchecks while retaining the framework's chosen application command.

## Verification

Write regression tests before implementing changes. Review snapshot changes against intended behavior; passing snapshots alone does not prove a runnable image.

`tests/test_generation.py` covers eight fixture stacks at both levels:

1. Output files exist and match snapshots.
2. `docker compose config` validates the generated configuration.
3. Docker builds the generated image.
4. The container serves HTTP on a dynamically allocated localhost port.
5. Full-mode healthchecks become healthy; static images exclude secrets and local dependencies.

Next.js and Vite fixtures use their real framework executables. React and Vue use small HTTP scripts for package installation, script invocation, ports, and permissions. Python fixtures are runnable applications.

`tests/test_regressions.py` covers entrypoints, overwrite protection, duplicate service names, YAML paths, manifest selection, ignore preservation/idempotency, and an offline npm development-dependency probe.

`tests/test_container_regressions.py` covers Python manifest formats, custom Flask and nested FastAPI entrypoints, and alternative Node package managers with Vite and Next.js.

```bash
uv sync --all-extras
SKIP_DOCKER_BUILD=1 uv run pytest
uv run pytest -n 2
uv run ruff check .
uv run ruff format --check .
```

The fast suite still requires the Docker CLI and Compose plugin. The full suite requires daemon access and network access for dependency downloads. Test containers are removed in cleanup; images remain tagged `yeetus-test-*`.

## Maintenance

Keep README.md, ARCHITECTURE.md, and ROADMAP.md aligned with implemented behavior. CHANGELOG.md is maintained by GitHub Actions.

Explicit shared network/volume configuration and cross-service environment configuration remain future work. Add new stacks through models, a registered detector, templates, runnable fixtures, and snapshot/runtime coverage.
