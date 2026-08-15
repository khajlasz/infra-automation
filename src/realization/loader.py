from pathlib import Path

from model.parser import parse_yaml
from realization.model import Realization


def load_realization(path: Path) -> Realization:
    """Load a deployment realization from YAML."""

    data = parse_yaml(path)

    return Realization(
        name=data["name"],
        docker=data.get("docker", {}),
        routeros=data.get("routeros", {}),
    )