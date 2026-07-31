"""Load declarative platform model files."""

from pathlib import Path
from typing import Any

import yaml

from model import (
    ApplicationDomain,
    ComputeDomain,
    ModelError,
    NetworkDomain,
    PlatformDomain,
    PlatformModel,
)
from model.discovery import discover_yaml_files
from observability import get_logger


logger = get_logger(__name__)


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML mapping from *path*."""
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if data is None:
        return {}
    if not isinstance(data, dict):
        logger.error("Expected a YAML mapping in %s", path)
        raise ModelError(f"Expected a YAML mapping in {path}")

    return data


class Loader:
    """Construct a platform model from a model directory."""

    @staticmethod
    def _unwrap_root_object(
        data: dict[str, Any], expected_root_key: str, path: Path
    ) -> Any:
        """Validate and remove the required self-describing root wrapper."""
        if len(data) != 1:
            logger.error(
                "Expected exactly one root key in %s, found %s.", path, len(data)
            )
            raise ModelError(
                f"Expected exactly one root key in {path}, found {len(data)}."
            )

        root_key = next(iter(data))
        if root_key != expected_root_key:
            logger.error(
                "Expected root key %r in %s, found %r.",
                expected_root_key,
                path,
                root_key,
            )
            raise ModelError(
                f"Expected root key {expected_root_key!r} in {path}, "
                f"found {root_key!r}."
            )

        return data[root_key]

    def load(self, model_directory: Path) -> PlatformModel:
        """Load all model YAML files under *model_directory*."""
        logger.info("Loading model from %s", model_directory)
        model = PlatformModel()
        loaded_file_count = 0
        domains = {
            "platform": model.platform,
            "network": model.network,
            "compute": model.compute,
            "application": model.application,
        }

        for path, relative_path in discover_yaml_files(model_directory):
            domain = domains.get(relative_path.parts[0])
            if domain is None or len(relative_path.parts) == 1:
                continue

            logger.info("Loading model file %s", relative_path)
            container = domain.data
            for directory in relative_path.parts[1:-1]:
            # Walk or create the nested dictionary structure corresponding to
            # the model subdirectories.
                container = container.setdefault(directory, {})

            attribute_name = path.stem.replace("-", "_")
            loaded_data = load_yaml(path)
            # The wrapper makes YAML self-describing. The internal model uses
            # the filename-derived attribute instead, so it can store its value.
            container[attribute_name] = self._unwrap_root_object(
                loaded_data, attribute_name, path
            )
            loaded_file_count += 1

        logger.info("Successfully loaded %s model files", loaded_file_count)
        return model
