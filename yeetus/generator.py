import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from yeetus.compose_builder import ComposeBuilder
from yeetus.detector import detect_stack
from yeetus.detector.python import detect_python_dependencies
from yeetus.models import ComposeConfig, ProjectPart, StackInfo

TEMPLATES_DIR = Path(__file__).parent / "templates"


class Generator:
    def __init__(self, templates_dir: Path | None = None):
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        # JSON strings are valid YAML scalars, including paths with YAML punctuation.
        self.env.filters["yaml_string"] = lambda value: json.dumps(
            str(value), ensure_ascii=False
        )

    def render_dockerfile(self, part: ProjectPart) -> str:
        template_name = f"{part.stack_info.stack_type}/Dockerfile.{part.level}.j2"
        template = self.env.get_template(template_name)
        dependency_source = "none"
        if part.stack_info.stack_type == "python":
            dependency_source = detect_python_dependencies(part.path)
            if (
                dependency_source == "uv"
                and not (part.path / "pyproject.toml").is_file()
            ):
                raise ValueError(
                    "uv.lock requires a pyproject.toml in the same project directory"
                )
        return template.render(
            port=part.get_target_port(),
            cmd=part.stack_info.cmd,
            framework=part.stack_info.framework,
            package_manager=part.stack_info.package_manager,
            package_manager_version=part.stack_info.package_manager_version,
            entrypoint=part.stack_info.entrypoint,
            dependency_source=dependency_source,
            uv_locked=(part.path / "uv.lock").is_file(),
            pipenv_locked=(part.path / "Pipfile.lock").is_file(),
        )

    def render_compose(self, compose_config: ComposeConfig) -> str:
        template = self.env.get_template("compose/compose.yaml.j2")
        return template.render(services=compose_config.services)

    def generate(
        self, root_dir: Path, parts: list[ProjectPart], dry_run: bool = False
    ) -> list[Path]:
        planned_files: dict[Path, str] = {}
        builder = ComposeBuilder(root_dir)
        compose_config = builder.build(parts)

        # Render every output before writing anything, so invalid services cannot
        # leave behind a partially overwritten project.
        for part in parts:
            part_dir = part.path
            dockerfile_content = self.render_dockerfile(part)
            dockerfile_path = part_dir / "Dockerfile"
            planned_files[dockerfile_path] = dockerfile_content

            exclusions = self.env.get_template("common/dockerignore.j2").render()
            ignore_paths = [part_dir / ".dockerignore"]
            specific_ignore = part_dir / "Dockerfile.dockerignore"
            if specific_ignore.exists():
                ignore_paths.append(specific_ignore)
            for ignore_path in ignore_paths:
                existing = (
                    ignore_path.read_text(encoding="utf-8")
                    if ignore_path.exists()
                    else ""
                )
                if existing.rstrip().endswith(exclusions.rstrip()):
                    planned_files[ignore_path] = existing
                else:
                    prefix = existing.rstrip() + "\n\n" if existing.strip() else ""
                    planned_files[ignore_path] = prefix + exclusions

            if part.level == "full" and part.stack_info.env_example:
                env_example_path = part_dir / ".env.example"
                planned_files[env_example_path] = part.stack_info.env_example

        # 2. Render and write unified compose.yaml at root_dir
        compose_content = self.render_compose(compose_config)
        compose_path = root_dir / "compose.yaml"
        planned_files[compose_path] = compose_content

        if not dry_run:
            for output_path, content in planned_files.items():
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(content, encoding="utf-8")

        return list(planned_files)


def generate_for_project(
    project_dir: Path,
    level: str = "minimal",
    service_name: str = "web",
    stack_info: StackInfo | None = None,
    dry_run: bool = False,
) -> list[Path]:
    if stack_info is None:
        stack_info = detect_stack(project_dir)
        if stack_info is None:
            raise ValueError(
                f"Could not auto-detect stack for directory: {project_dir}"
            )

    part = ProjectPart(
        name=service_name,
        path=project_dir,
        stack_info=stack_info,
        level=level,
    )

    generator = Generator()
    return generator.generate(root_dir=project_dir, parts=[part], dry_run=dry_run)
