import json
from dataclasses import dataclass, field, replace
from pathlib import Path


@dataclass
class StackInfo:
    stack_type: str  # 'python', 'node', 'static'
    framework: (
        str  # 'flask', 'fastapi', 'django', 'nextjs', 'react', 'vite', 'vue', 'static'
    )
    port: int
    cmd: str
    env_example: str = ""
    description: str = ""
    package_manager: str = "npm"  # 'npm', 'pnpm', 'yarn', 'bun'
    entrypoint: str = ""
    package_manager_version: str = ""

    def with_entrypoint(self, entrypoint: str) -> "StackInfo":
        if not entrypoint or self.stack_type != "python":
            return self
        new_env = self.env_example
        if self.framework == "fastapi":
            entrypoint_path = Path(entrypoint)
            if entrypoint_path.is_absolute() or ".." in entrypoint_path.parts:
                raise ValueError(
                    "FastAPI entrypoints must be relative to the project directory"
                )
            module = entrypoint_path.with_suffix("").as_posix().replace("/", ".")
            cmd = json.dumps(
                [
                    "uvicorn",
                    f"{module}:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    str(self.port),
                ]
            )
        elif self.framework == "django":
            cmd = json.dumps(
                ["python", entrypoint, "runserver", f"0.0.0.0:{self.port}"]
            )
        elif self.framework == "flask":
            cmd = json.dumps(
                [
                    "python",
                    "-m",
                    "flask",
                    "--app",
                    entrypoint,
                    "run",
                    "--host=0.0.0.0",
                    f"--port={self.port}",
                ]
            )
            new_env = (
                f"FLASK_APP={entrypoint}\nFLASK_ENV=production\nPORT={self.port}\n"
            )
        else:
            cmd = json.dumps(["python", entrypoint])

        return replace(self, cmd=cmd, env_example=new_env, entrypoint=entrypoint)

    def with_package_manager(self, package_manager: str) -> "StackInfo":
        if self.stack_type != "node":
            return self
        args = (
            ["dev", "--host"]
            if self.framework == "vite"
            else ["serve"]
            if self.framework == "vue"
            else ["start"]
        )
        runner = (
            ["bun", "run"]
            if package_manager == "bun"
            else [package_manager]
            if args == ["start"]
            else [package_manager, "run"]
        )
        cmd = (
            json.dumps(runner + args)
            if package_manager in ("pnpm", "yarn", "bun")
            else self.cmd
        )
        desc = (
            f"{self.description} [{package_manager}]"
            if package_manager != "npm" and self.description
            else self.description
        )
        return replace(self, cmd=cmd, description=desc, package_manager=package_manager)


@dataclass
class ProjectPart:
    name: str
    path: Path
    stack_info: StackInfo
    level: str = "minimal"  # 'minimal' or 'full'
    port: int | None = None
    target_port: int | None = None
    env_file: str | None = None
    depends_on: list[str] = field(default_factory=list)
    restart: str | None = None

    def get_port(self) -> int:
        return self.port if self.port is not None else self.stack_info.port

    def get_target_port(self) -> int:
        return self.target_port if self.target_port is not None else self.get_port()


@dataclass
class ComposeServiceConfig:
    name: str
    context: str
    dockerfile: str = "Dockerfile"
    port: int = 80
    target_port: int = 80
    env_file: str | None = None
    depends_on: list[str] = field(default_factory=list)
    restart: str | None = None


@dataclass
class ComposeConfig:
    services: list[ComposeServiceConfig] = field(default_factory=list)
