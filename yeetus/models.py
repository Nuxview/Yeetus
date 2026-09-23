from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

@dataclass
class StackInfo:
    stack_type: str  # 'python', 'node', 'static'
    framework: str   # 'flask', 'fastapi', 'django', 'nextjs', 'react', 'vite', 'vue', 'static'
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
    port: Optional[int] = None
    target_port: Optional[int] = None
    env_file: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)
    restart: Optional[str] = None

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
    env_file: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)
    restart: Optional[str] = None

@dataclass
class ComposeConfig:
    services: List[ComposeServiceConfig] = field(default_factory=list)
    networks: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)
