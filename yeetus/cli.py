from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from yeetus import __version__
from yeetus.compose_builder import PortCollisionError
from yeetus.detector import detect_stack
from yeetus.generator import Generator
from yeetus.models import ProjectPart, StackInfo

app = typer.Typer(
    name="yeetus",
    help="Yeetus: Open-source alternative to docker init with multi-service support, auto-detection, and compose wiring.",
    no_args_is_help=False,
)

console = Console()

FRAMEWORK_CATALOG = {
    "flask": StackInfo(
        stack_type="python",
        framework="flask",
        port=5000,
        cmd='["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]',
        env_example="FLASK_APP=app.py\nFLASK_ENV=production\nPORT=5000\n",
        description="Python (Flask)",
    ),
    "fastapi": StackInfo(
        stack_type="python",
        framework="fastapi",
        port=8000,
        cmd='["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]',
        env_example="PORT=8000\nHOST=0.0.0.0\n",
        description="Python (FastAPI)",
    ),
    "django": StackInfo(
        stack_type="python",
        framework="django",
        port=8000,
        cmd='["python", "manage.py", "runserver", "0.0.0.0:8000"]',
        env_example="SECRET_KEY=change-me-in-production\nDEBUG=False\nALLOWED_HOSTS=localhost,127.0.0.1\nPORT=8000\n",
        description="Python (Django)",
    ),
    "nextjs": StackInfo(
        stack_type="node",
        framework="nextjs",
        port=3000,
        cmd='["npm", "start"]',
        env_example="NODE_ENV=production\nPORT=3000\n",
        description="Node.js (Next.js)",
    ),
    "react": StackInfo(
        stack_type="node",
        framework="react",
        port=3000,
        cmd='["npm", "start"]',
        env_example="NODE_ENV=production\nPORT=3000\n",
        description="Node.js (React)",
    ),
    "vite": StackInfo(
        stack_type="node",
        framework="vite",
        port=5173,
        cmd='["npm", "run", "dev", "--", "--host"]',
        env_example="NODE_ENV=production\nPORT=5173\n",
        description="Node.js (Vite)",
    ),
    "vue": StackInfo(
        stack_type="node",
        framework="vue",
        port=8080,
        cmd='["npm", "run", "serve"]',
        env_example="NODE_ENV=production\nPORT=8080\n",
        description="Node.js (Vue)",
    ),
    "static": StackInfo(
        stack_type="static",
        framework="static",
        port=80,
        cmd='["nginx", "-g", "daemon off;"]',
        env_example="PORT=80\n",
        description="Static HTML (Nginx)",
    ),
}


def version_callback(value: bool):
    if value:
        console.print(
            f"[bold cyan]Yeetus[/bold cyan] version [bold green]{__version__}[/bold green]"
        )
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            help="Show Yeetus version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
):
    """Yeetus CLI tool."""


@app.command()
def init(
    path: Annotated[
        Path | None,
        typer.Argument(
            help="Target project directory (default: current working directory)",
        ),
    ] = None,
    level: Annotated[
        str | None,
        typer.Option(
            "--level",
            "-l",
            help="Boilerplate level: 'minimal' or 'full'",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Preview generated files without writing to disk",
        ),
    ] = False,
    no_detection: Annotated[
        bool,
        typer.Option(
            "--no-detection",
            help="Skip auto-detection and prompt manually for tech stack",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite existing files without prompting",
        ),
    ] = False,
    multi: Annotated[
        bool,
        typer.Option(
            "--multi",
            "-m",
            help="Configure a multi-service project",
        ),
    ] = False,
    readme: Annotated[
        bool,
        typer.Option(
            "--readme/--no-readme",
            help="Generate README.docker.md documentation",
        ),
    ] = True,
    entrypoint: Annotated[
        str | None,
        typer.Option(
            "--entrypoint",
            "-e",
            help="Main Python entrypoint file (e.g. app.py, main.py, manage.py)",
        ),
    ] = None,
):
    """Initialize Dockerfile and unified compose.yaml for a project."""
    root_dir = (path or Path.cwd()).resolve()

    console.print(
        Panel.fit(
            f"[bold cyan]Yeetus[/bold cyan] [dim]v{__version__}[/dim]\n"
            f"[white]Target directory:[/white] [green]{root_dir}[/green]",
            border_style="cyan",
        )
    )

    parts: list[ProjectPart] = []

    # Check if multi-service mode
    is_multi = multi
    if not is_multi and not level:
        # Ask interactively if not specified
        try:
            is_multi = Confirm.ask("Is this a multi-service project?", default=False)
        except (EOFError, OSError):
            is_multi = False

    if is_multi:
        console.print("\n[bold]Configuring multi-service project...[/bold]")
        part_idx = 1
        while True:
            console.print(f"\n[bold cyan]--- Service #{part_idx} ---[/bold cyan]")
            default_name = f"service{part_idx}"
            service_name = Prompt.ask("Service name", default=default_name)
            subpath_str = Prompt.ask(
                "Subdirectory path (relative to root)", default=service_name
            )
            part_dir = (root_dir / subpath_str).resolve()

            stack_info = _resolve_stack(part_dir, no_detection)
            if stack_info.stack_type == "python":
                py_file = _resolve_python_entrypoint(
                    part_dir, stack_info.framework, entrypoint
                )
                stack_info = stack_info.with_entrypoint(py_file)

            part_level = _resolve_level(level)
            port_str = Prompt.ask("Port to expose", default=str(stack_info.port))
            port = int(port_str)

            # Depends on
            existing_services = [p.name for p in parts]
            depends_on: list[str] = []
            if existing_services:
                dep_choices = ", ".join(existing_services)
                dep_input = Prompt.ask(
                    f"Depends on other services? (comma-separated, available: {dep_choices})",
                    default="",
                )
                if dep_input.strip():
                    depends_on = [
                        d.strip()
                        for d in dep_input.split(",")
                        if d.strip() in existing_services
                    ]

            parts.append(
                ProjectPart(
                    name=service_name,
                    path=part_dir,
                    stack_info=stack_info,
                    level=part_level,
                    port=port,
                    depends_on=depends_on,
                )
            )

            if not Confirm.ask("Add another service?", default=False):
                break
            part_idx += 1
    else:
        # Single service
        service_name = "web"
        stack_info = _resolve_stack(root_dir, no_detection)
        if stack_info.stack_type == "python":
            py_file = _resolve_python_entrypoint(
                root_dir, stack_info.framework, entrypoint
            )
            stack_info = stack_info.with_entrypoint(py_file)

        part_level = _resolve_level(level)
        parts.append(
            ProjectPart(
                name=service_name,
                path=root_dir,
                stack_info=stack_info,
                level=part_level,
            )
        )

    # Check for file conflicts
    if not force and not dry_run:
        conflicts = []
        for part in parts:
            df = part.path / "Dockerfile"
            if df.exists():
                conflicts.append(df)
            if part.level == "full":
                env_file = part.path / ".env.example"
                if env_file.exists():
                    conflicts.append(env_file)
        compose_file = root_dir / "compose.yaml"
        if compose_file.exists():
            conflicts.append(compose_file)

        if conflicts:
            console.print(
                "\n[bold yellow]Warning: The following files already exist:[/bold yellow]"
            )
            for c in conflicts:
                console.print(f"  • [yellow]{c}[/yellow]")
            if not Confirm.ask("Do you want to overwrite them?", default=False):
                console.print("[red]Aborted by user.[/red]")
                raise typer.Abort()

    # Generate files
    generator = Generator()
    try:
        generated_files = generator.generate(root_dir, parts, dry_run=dry_run)
    except PortCollisionError as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Generate README if requested
    if readme and not dry_run:
        readme_path = _generate_readme(root_dir, parts)
        generated_files.append(readme_path)

    # Print summary table
    table = Table(
        title="Generated Files" if not dry_run else "Dry Run Preview (No files written)"
    )
    table.add_column("File Path", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Status", style="magenta")

    for f in generated_files:
        try:
            rel = f.relative_to(root_dir)
        except ValueError:
            rel = f
        table.add_row(str(rel), f.name, "Previewed" if dry_run else "Created")

    console.print()
    console.print(table)
    console.print("\n[bold green]Success![/bold green] Next steps:")
    console.print(
        "  1. Run [cyan]docker compose up --build[/cyan] to start your application."
    )
    if any(p.level == "full" for p in parts):
        console.print(
            "  2. Review [cyan].env.example[/cyan] and create [cyan].env[/cyan] if needed."
        )


def _resolve_stack(path: Path, no_detection: bool) -> StackInfo:
    if not no_detection:
        detected = detect_stack(path)
        if detected:
            console.print(
                f"[green]✓ Detected:[/green] [bold]{detected.description}[/bold]"
            )
            try:
                if Confirm.ask("Use this detected tech stack?", default=True):
                    return detected
            except (EOFError, OSError):
                return detected

    # Manual selection
    console.print("[yellow]Please select your framework:[/yellow]")
    framework_list = list(FRAMEWORK_CATALOG.keys())
    for idx, fw in enumerate(framework_list, start=1):
        info = FRAMEWORK_CATALOG[fw]
        console.print(f"  {idx}) [bold]{fw}[/bold] ({info.description})")

    choice = Prompt.ask("Choose framework", choices=framework_list, default="flask")
    return FRAMEWORK_CATALOG[choice]


def _resolve_python_entrypoint(
    part_dir: Path,
    framework: str,
    entrypoint_opt: str | None = None,
) -> str:
    if entrypoint_opt and entrypoint_opt.strip():
        return entrypoint_opt.strip()

    if framework == "fastapi":
        default_file = "main.py"
    elif framework == "django":
        default_file = "manage.py"
    else:
        default_file = "app.py"

    # If default_file does not exist in part_dir, check if any of the other standard files exist
    if not (part_dir / default_file).exists():
        for candidate in ("app.py", "manage.py", "main.py"):
            if (part_dir / candidate).exists():
                default_file = candidate
                break

    try:
        ans = Prompt.ask("Main Python entrypoint file", default=default_file)
        return ans.strip() if ans and ans.strip() else default_file
    except (EOFError, OSError):
        return default_file


def _resolve_level(level_opt: str | None) -> str:
    if level_opt and level_opt.lower() in ("minimal", "full"):
        return level_opt.lower()
    try:
        return Prompt.ask(
            "Select boilerplate level",
            choices=["minimal", "full"],
            default="minimal",
        )
    except (EOFError, OSError):
        return "minimal"


def _generate_readme(root_dir: Path, parts: list[ProjectPart]) -> Path:
    lines = [
        "# Docker Configuration (Generated by Yeetus)",
        "",
        "This project has been scaffolded with Docker and Docker Compose support.",
        "",
        "## Services",
        "",
    ]
    for p in parts:
        lines.append(
            f"- **{p.name}**: {p.stack_info.description} on port `{p.get_port()}` (level: `{p.level}`)"
        )
    lines.extend(
        [
            "",
            "## Quick Start",
            "",
            "Build and run all services:",
            "```bash",
            "docker compose up --build",
            "```",
            "",
            "Stop all services:",
            "```bash",
            "docker compose down",
            "```",
        ]
    )
    readme_path = root_dir / "README.docker.md"
    readme_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return readme_path


if __name__ == "__main__":
    app()
