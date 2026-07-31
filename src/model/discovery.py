"""Discover YAML files that belong to a platform model."""

from pathlib import Path


def discover_yaml_files(model_directory: Path) -> list[tuple[Path, Path]]:
    """Return sorted absolute model paths together with their relative paths."""
    model_root = model_directory.resolve()
    return [
        (path, path.relative_to(model_root))
        for path in sorted(model_root.rglob("*.yaml"))
    ]
