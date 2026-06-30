"""Builds a unified ComposeConfig from a list of ProjectParts."""

from __future__ import annotations

from open_di.models import ComposeConfig, ComposeService, ProjectPart, Stack


class PortCollisionError(ValueError):
    """Raised when two services claim the same host port."""


def build_compose_config(parts: list[ProjectPart]) -> ComposeConfig:
    """Construct a :class:`~open_di.models.ComposeConfig` from *parts*.

    Each part becomes one compose service. The build context is set to the
    part's relative path so compose.yaml references sit correctly alongside
    the generated Dockerfiles.

    Args:
        parts: Ordered list of configured project parts.

    Returns:
        A fully populated :class:`~open_di.models.ComposeConfig`.

    Raises:
        PortCollisionError: If two parts declare the same host port.
    """
    config = ComposeConfig()
    used_ports: dict[int, str] = {}  # port → service name

    for part in parts:
        if part.port is not None:
            if part.port in used_ports:
                raise PortCollisionError(
                    f"Service '{part.name}' wants port {part.port} but it is "
                    f"already claimed by service '{used_ports[part.port]}'."
                )
            used_ports[part.port] = part.name

        # nginx always listens on port 80 inside the container; the user's
        # chosen port is the host side of the mapping.
        container_port = 80 if part.stack_info.stack == Stack.STATIC else None

        service = ComposeService(
            name=part.name,
            build_context=part.path,
            port=part.port,
            container_port=container_port,
            env_vars=dict(part.env_vars),
        )
        config.services.append(service)

    return config
