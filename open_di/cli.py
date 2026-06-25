"""CLI entry point for open-di."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from open_di import __version__
from open_di.compose_builder import PortCollisionError, build_compose_config
from open_di.detector import detect_stack
from open_di.generator import Generator
from open_di.models import BoilerplateLevel, ProjectPart, Stack, StackInfo

app = typer.Typer(
    name="open-di",
    help="Open-source alternative to docker init. Scaffolds Dockerfiles and a unified compose.yaml.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


# ── Commands ──────────────────────────────────────────────────────────────────


@app.command()
def init(
    root: Optional[Path] = typer.Option(
        None,
        "--root",
        "-r",
        help="Project root directory. Defaults to the current directory.",
        show_default=False,
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be generated without writing any files.",
    ),
) -> None:
    """Interactively scaffold Dockerfiles and a unified compose.yaml."""

    project_root = (root or Path.cwd()).resolve()

    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]open-di[/bold cyan]  [dim]v{__version__}[/dim]\n"
            f"Scaffolding [bold]{project_root.name}[/bold]  "
            f"[dim]{project_root}[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    parts: list[ProjectPart] = []
    used_ports: set[int] = set()

    # ── How many services? ────────────────────────────────────────────────
    count = IntPrompt.ask(
        "[bold]How many services / parts does your project have?[/bold]",
        default=1,
        console=console,
    )

    for i in range(1, count + 1):
        console.print()
        console.rule(f"[bold cyan]Service {i} of {count}[/bold cyan]")
        part = _configure_part(project_root, used_ports, index=i)
        if part.port is not None:
            used_ports.add(part.port)
        parts.append(part)

    # ── Summary table ─────────────────────────────────────────────────────
    _print_summary(parts)

    if not Confirm.ask("\n[bold]Generate files?[/bold]", default=True, console=console):
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit()

    # ── Generate ──────────────────────────────────────────────────────────
    console.print()
    console.rule("[bold cyan]Generating[/bold cyan]")

    try:
        compose_config = build_compose_config(parts)
    except PortCollisionError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1)

    generator = Generator()

    for part in parts:
        target = Path(part.path) / "Dockerfile"
        if dry_run:
            console.print(f"  [dim](dry-run)[/dim] would write [bold]{target}[/bold]")
        else:
            output = generator.render_dockerfile(part, project_root)
            console.print(f"  [green]✓[/green] {output.relative_to(project_root)}")

    compose_target = Path("compose.yaml")
    if dry_run:
        console.print(
            f"  [dim](dry-run)[/dim] would write [bold]{compose_target}[/bold]"
        )
    else:
        compose_out = generator.render_compose(compose_config, project_root)
        console.print(f"  [green]✓[/green] {compose_out.relative_to(project_root)}")

    console.print()
    if dry_run:
        console.print("[yellow]Dry-run complete — no files were written.[/yellow]")
    else:
        console.print(
            "[bold green]Done![/bold green]  "
            "Build and start your project:\n\n"
            "  [bold]docker compose up --build[/bold]\n"
        )


# ── Interactive helpers ────────────────────────────────────────────────────────


def _configure_part(
    project_root: Path,
    used_ports: set[int],
    index: int,
) -> ProjectPart:
    """Interactively collect configuration for one project part/service."""

    # Name
    default_name = f"service{index}"
    name = Prompt.ask(
        "  [bold]Name[/bold]",
        default=default_name,
        console=console,
    ).strip()

    # Path
    default_path = f"./{name}"
    raw_path = Prompt.ask(
        "  [bold]Path[/bold] (relative to project root)",
        default=default_path,
        console=console,
    ).strip()

    service_path = _normalise_path(raw_path)
    abs_path = (project_root / service_path).resolve()

    # Stack detection
    stack_info = _resolve_stack(abs_path, service_path)

    # Port
    port = _ask_port(used_ports)

    # Boilerplate level
    level_str = Prompt.ask(
        "  [bold]Boilerplate level[/bold]",
        choices=["minimal", "full"],
        default="minimal",
        console=console,
    )
    boilerplate = BoilerplateLevel(level_str)

    return ProjectPart(
        name=name,
        path=str(service_path),
        stack_info=stack_info,
        boilerplate=boilerplate,
        port=port,
    )


def _resolve_stack(abs_path: Path, display_path: Path) -> StackInfo:
    """Auto-detect the stack and let the user confirm or override."""
    detected: Optional[StackInfo] = None

    if abs_path.exists():
        with console.status(
            f"  Detecting stack in [dim]{display_path}[/dim]…", spinner="dots"
        ):
            detected = detect_stack(abs_path)

    if detected is not None:
        console.print(f"  [green]✓[/green] Detected: [bold]{detected.display()}[/bold]")
        if Confirm.ask("  Confirm detected stack?", default=True, console=console):
            return detected
        # User declined — fall through to manual entry
        console.print()

    else:
        if abs_path.exists():
            console.print(
                f"  [yellow]![/yellow] Could not auto-detect a stack in "
                f"[dim]{display_path}[/dim]."
            )
        else:
            console.print(
                f"  [yellow]![/yellow] [dim]{display_path}[/dim] does not exist yet. "
                "Specify the stack manually."
            )

    return _ask_stack_manually()


def _ask_stack_manually() -> StackInfo:
    """Prompt the user to fully describe a stack."""
    stack_str = Prompt.ask(
        "  [bold]Stack[/bold]",
        choices=["python", "node", "go"],
        console=console,
    )
    stack = Stack(stack_str)

    version = (
        Prompt.ask(
            "  [bold]Runtime version[/bold] [dim](blank = use default)[/dim]",
            default="",
            console=console,
        ).strip()
        or None
    )

    framework = (
        Prompt.ask(
            "  [bold]Framework[/bold] [dim](blank = none)[/dim]",
            default="",
            console=console,
        ).strip()
        or None
    )

    pkg_choices: list[str] = {
        Stack.PYTHON: ["pip", "uv", "poetry"],
        Stack.NODE: ["npm", "yarn", "pnpm"],
        Stack.GO: [],
    }.get(stack, [])

    package_manager: Optional[str] = None
    if pkg_choices:
        package_manager = Prompt.ask(
            "  [bold]Package manager[/bold]",
            choices=pkg_choices,
            default=pkg_choices[0],
            console=console,
        )

    return StackInfo(
        stack=stack,
        version=version,
        framework=framework,
        package_manager=package_manager,
    )


def _ask_port(used_ports: set[int]) -> Optional[int]:
    """Ask for a host port, repeating on collisions or bad input."""
    while True:
        raw = Prompt.ask(
            "  [bold]Port[/bold] [dim](blank to skip)[/dim]",
            default="",
            console=console,
        ).strip()
        if not raw:
            return None
        try:
            port = int(raw)
        except ValueError:
            console.print("  [red]Please enter a valid port number.[/red]")
            continue
        if port in used_ports:
            console.print(
                f"  [yellow]![/yellow] Port [bold]{port}[/bold] is already "
                "assigned to another service — pick a different one."
            )
            continue
        return port


def _normalise_path(raw: str) -> Path:
    """Ensure the path starts with './' for predictable compose contexts."""
    p = Path(raw)
    if not str(p).startswith("."):
        p = Path(".") / p
    return p


def _print_summary(parts: list[ProjectPart]) -> None:
    """Print a Rich table showing all configured services before writing."""
    table = Table(
        title="Service Configuration",
        border_style="cyan",
        show_lines=True,
        title_style="bold cyan",
    )
    table.add_column("Name", style="bold")
    table.add_column("Path", style="dim")
    table.add_column("Stack")
    table.add_column("Level")
    table.add_column("Port", justify="right")

    for p in parts:
        table.add_row(
            p.name,
            p.path,
            p.stack_info.display(),
            p.boilerplate.value,
            str(p.port) if p.port is not None else "[dim]—[/dim]",
        )

    console.print()
    console.print(table)


def main() -> None:
    app()
