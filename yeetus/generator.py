from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from yeetus.compose_builder import ComposeBuilder
from yeetus.detector import detect_stack
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

    def render_dockerfile(self, part: ProjectPart) -> str:
        template_name = f"{part.stack_info.stack_type}/Dockerfile.{part.level}.j2"
        template = self.env.get_template(template_name)
        return template.render(
            port=part.get_target_port(),
            cmd=part.stack_info.cmd,
            framework=part.stack_info.framework,
            package_manager=part.stack_info.package_manager,
            entrypoint=part.stack_info.entrypoint,
        )

    def render_compose(self, compose_config: ComposeConfig) -> str:
        template = self.env.get_template("compose/compose.yaml.j2")
        return template.render(services=compose_config.services)

    def generate(
        self, root_dir: Path, parts: list[ProjectPart], dry_run: bool = False
    ) -> list[Path]:
        generated_files: list[Path] = []
        builder = ComposeBuilder(root_dir)
        compose_config = builder.build(parts)

        # 1. Render and write Dockerfile & .env.example for each part
        for part in parts:
            part_dir = part.path
            dockerfile_content = self.render_dockerfile(part)
            dockerfile_path = part_dir / "Dockerfile"
            if not dry_run:
                part_dir.mkdir(parents=True, exist_ok=True)
                dockerfile_path.write_text(dockerfile_content, encoding="utf-8")
            generated_files.append(dockerfile_path)

            if part.level == "full" and part.stack_info.env_example:
                env_example_path = part_dir / ".env.example"
                if not dry_run:
                    env_example_path.write_text(
                        part.stack_info.env_example, encoding="utf-8"
                    )
                generated_files.append(env_example_path)

        # 2. Render and write unified compose.yaml at root_dir
        compose_content = self.render_compose(compose_config)
        compose_path = root_dir / "compose.yaml"
        if not dry_run:
            compose_path.write_text(compose_content, encoding="utf-8")
        generated_files.append(compose_path)

        return generated_files


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
