from dataclasses import dataclass, field
from typing import Any


@dataclass
class Realization:
    """Environment-specific deployment realization."""

    name: str
    docker: dict[str, Any] = field(default_factory=dict)
    routeros: dict[str, Any] = field(default_factory=dict)
