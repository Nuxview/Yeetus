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
