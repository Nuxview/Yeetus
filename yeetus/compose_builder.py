import os
from pathlib import Path

from yeetus.models import ComposeConfig, ComposeServiceConfig, ProjectPart


class PortCollisionError(ValueError):
    """Raised when multiple project parts are assigned the same host port."""


class ComposeBuilder:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def build(self, parts: list[ProjectPart]) -> ComposeConfig:
        allocated_ports: dict[int, str] = {}
        services: list[ComposeServiceConfig] = []

        for part in parts:
            host_port = part.get_port()
            if host_port in allocated_ports:
                prev_part = allocated_ports[host_port]
                raise PortCollisionError(
                    f"Port collision detected: port {host_port} is already used by '{prev_part}' but also requested by '{part.name}'"
                )
            allocated_ports[host_port] = part.name

            context = os.path.relpath(part.path.resolve(), self.root_dir.resolve())
            env_file = (
                (".env" if context == "." else f"{context}/.env")
                if part.level == "full"
                else None
            )

            service = ComposeServiceConfig(
                name=part.name,
                context=context,
                dockerfile="Dockerfile",
                port=host_port,
                target_port=part.get_target_port(),
                env_file=env_file,
                depends_on=part.depends_on,
                restart="unless-stopped" if part.level == "full" else None,
            )
            services.append(service)

        return ComposeConfig(services=services)
