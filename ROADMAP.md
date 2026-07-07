# Roadmap
This document outlines the roadmap for the Open-DI project.
Currently, the project is divided into four phases.

> DISCLAIMER: 
> a. This roadmap is a work in progress and may change.
> b. I WILL NOT add support for the following frameworks/languages as I've never used them:
>   1. Python
>     - Django
>     - Uvicorn
>     - Tornado
>     - sanic
>     - Starlette
>     - litestar
>   2. JavaScript/TypeScript
>     - nuxt
>     - express
>     - astro
>     - Svelte
>     - fastify
>     - remix
>     - koa
>   3. Go
>   4. C/C++
>   5. Java
>   6. Rust

## Phase 1 (In Progress)
This phase primarily focuses on project scaffolding with some common languages and frameworks.

Languages supported in this phase include:
- Python
- JavaScript/TypeScript
- Static HTML/CSS

Frameworks supported in this phase include:
- Python
  - Flask
  - FastAPI
- JavaScript/TypeScript
  - Next.js
  - React
  - Vue.js
  - Vite
- Static HTML/CSS
  - Plain HTML/CSS

Here is the current project overview along with a one-liner on what each file does:

```text
.
├── .github
│   └── workflows
│       ├── changelog.yml                 # Updates CHANGELOG.md
│       └── ci.yml                        # Runs linting and tests
│
├── open_di
│   ├── detector
│   │   ├── __init__.py                   # Runs stack detection
│   │   ├── base.py                       # Base stack detection logic imported by other detectors
│   │   ├── node.py                       # Node.js stack detection logic
│   │   ├── python.py                     # Python stack detection logic
│   │   └── static.py                     # Static HTML/CSS stack detection logic
│   │
│   ├── templates                         # Jinja2 templates for generating Docker Compose files
│   │   ├── compose
│   │   │   └── compose.yaml.j2           # Compose template
│   │   ├── node
│   │   │   ├── Dockerfile.full.j2        # Full Node.js Dockerfile template
│   │   │   └── Dockerfile.minimal.j2     # Minimal Node.js Dockerfile template
│   │   ├── python
│   │   │   ├── Dockerfile.full.j2        # Full Python Dockerfile template
│   │   │   └── Dockerfile.minimal.j2     # Minimal Python Dockerfile template  
│   │   └── static
│   │       ├── Dockerfile.full.j2        # Full static Dockerfile template
│   │       └── Dockerfile.minimal.j2     # Minimal static Dockerfile template
│   │
│   ├── __init__.py                       # Curently only has the project version
│   ├── __main__.py                       # Runs the CLI
│   ├── cli.py                            # CLI entry point
│   ├── compose_builder.py                # Creates docker compose configs
│   ├── generator.py                      # Generates Docker Compose files from templates
│   └── models.py                         # Data models for the CLI. Also has classes for representing Docker Compose configurations.
│
├── .gitignore                            # Git ignore file
├── .projtreeignore                       # Project tree ignore file
├── CHANGELOG.md                          # Changelog for the project
├── CONTRIBUTING.md                       # Contribution guidelines for the project
├── LICENSE                               # License file for the project
├── pyproject.toml                        # Project configuration file
├── README.md                             # Project README file
├── ROADMAP.md                            # This file
└── uv.lock                               # Lock file for the project dependencies
```

### Yet to be implemented
1. Tests for each of the stack types. I'm talking bout both minimal and full templates generation.
2. Prompt to pull or build the docker image for the stack type

### Exit Criteria
1. Correct stack detection for python, node, and static html files
2. Correct dockerfile generation (both minimal and full)
3. Correct docker compose wiring (excluding networks, volumes, env and environment)
4. All soon to be created tests passing

## Phase 2 (Planned)
We only care about `env` related entries in this phase.
That is, wiring up:
1. `.env.example` generation
2. `env` variable references across services
3. `environment` variable references across services

## Phase 3 (Planned)
| 3 | Planned | `depends_on` wiring · shared networks & volumes · cross-service env refs |

## Phase 4 (Planned)
| 4 | Planned | `open-di init add` to append services to an existing compose.yaml |

---
