"""Renders Jinja2 templates to Dockerfile and compose.yaml files on disk."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from open_di.models import ComposeConfig, ProjectPart, Stack

_TEMPLATES_DIR = Path(__file__).parent / "templates"

# Sensible runtime version defaults when the detector cannot pin one.
_DEFAULT_VERSIONS: dict[Stack, str] = {
    Stack.PYTHON: "3.14",
    Stack.NODE: "24",
    Stack.STATIC: "stable-alpine",
}


class Generator:
    """Renders Jinja2 templates to Dockerfile and compose.yaml files."""

    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            # trim_blocks removes the first newline after a block tag so that
            # {% if %}…{% endif %} sections don't leave blank lines.
            trim_blocks=True,
            # lstrip_blocks strips leading whitespace from block-tag lines,
            # keeping the rendered output free of spurious indentation.
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    def render_dockerfile(self, part: ProjectPart, project_root: Path) -> Path:
        """Render a Dockerfile for *part* and write it into the service directory.

        Args:
            part: Configured project part.
            project_root: Absolute path to the root of the project.

        Returns:
            The absolute path of the written Dockerfile.

        Raises:
            FileNotFoundError: When no template exists for the given stack/level.
        """
        stack = part.stack_info.stack
        level = part.boilerplate.value
        template_name = f"{stack.value}/Dockerfile.{level}.j2"

        try:
            template = self._env.get_template(template_name)
        except TemplateNotFound:
            raise FileNotFoundError(
                f"No template found for stack '{stack.value}', level '{level}'. "
                f"Expected: open_di/templates/{template_name}"
            )

        context: dict = {
            "version": part.stack_info.version
            or _DEFAULT_VERSIONS.get(stack, "latest"),
            "framework": part.stack_info.framework,
            "package_manager": part.stack_info.package_manager,
            "port": part.port,
            **part.stack_info.extras,
        }

        rendered = template.render(**context)
        output_path = project_root / part.path / "Dockerfile"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered)
        return output_path

    def render_compose(self, config: ComposeConfig, project_root: Path) -> Path:
        """Render a compose.yaml from *config* and write it to *project_root*.

        Args:
            config: Populated ComposeConfig object.
            project_root: Absolute path to the root of the project.

        Returns:
            The absolute path of the written compose.yaml.
        """
        template = self._env.get_template("compose/compose.yaml.j2")
        rendered = template.render(config=config)
        output_path = project_root / "compose.yaml"
        output_path.write_text(rendered)
        return output_path
