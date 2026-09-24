from dataclasses import dataclass, field
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

    def with_entrypoint(self, entrypoint: str) -> "StackInfo":
        if not entrypoint or self.stack_type != "python":
            return self
        new_cmd = self.cmd
        new_env = self.env_example
        if self.framework == "fastapi":
            stem = Path(entrypoint).stem
            new_cmd = f'["uvicorn", "{stem}:app", "--host", "0.0.0.0", "--port", "{self.port}"]'
        elif self.framework == "django":
            new_cmd = f'["python", "{entrypoint}", "runserver", "0.0.0.0:{self.port}"]'
        elif self.framework == "flask":
            new_cmd = f'["python", "-m", "flask", "run", "--host=0.0.0.0", "--port={self.port}"]'
            new_env = (
                f"FLASK_APP={entrypoint}\nFLASK_ENV=production\nPORT={self.port}\n"
            )
        else:
            new_cmd = f'["python", "{entrypoint}"]'

        return StackInfo(
            stack_type=self.stack_type,
            framework=self.framework,
            port=self.port,
            cmd=new_cmd,
            env_example=new_env,
            description=self.description,
            package_manager=self.package_manager,
            entrypoint=entrypoint,
        )

    def with_package_manager(self, package_manager: str) -> "StackInfo":
        if self.stack_type != "node":
            return self
        cmd = self.cmd
        if package_manager in ("pnpm", "yarn", "bun"):
            if self.framework in ("nextjs", "react"):
                if package_manager == "bun":
                    cmd = '["bun", "run", "start"]'
                else:
                    cmd = f'["{package_manager}", "start"]'
            elif self.framework == "vite":
                if package_manager == "bun":
                    cmd = '["bun", "run", "dev", "--host"]'
                else:
                    cmd = f'["{package_manager}", "run", "dev", "--host"]'
            elif self.framework == "vue":
                if package_manager == "bun":
                    cmd = '["bun", "run", "serve"]'
                else:
                    cmd = f'["{package_manager}", "run", "serve"]'
            elif package_manager == "bun":
                cmd = '["bun", "run", "start"]'
            else:
                cmd = f'["{package_manager}", "start"]'

        desc = self.description
        if package_manager != "npm" and desc:
            desc = f"{desc} [{package_manager}]"

        return StackInfo(
            stack_type=self.stack_type,
            framework=self.framework,
            port=self.port,
            cmd=cmd,
            env_example=self.env_example,
            description=desc,
            package_manager=package_manager,
            entrypoint=self.entrypoint,
        )


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
    volumes: list[str] = field(default_factory=list)
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
    volumes: list[str] = field(default_factory=list)
    restart: str | None = None


@dataclass
class ComposeConfig:
    services: list[ComposeServiceConfig] = field(default_factory=list)
    networks: list[str] = field(default_factory=list)
    volumes: list[str] = field(default_factory=list)
