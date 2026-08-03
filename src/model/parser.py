"""YAML parsing module for the Infrastructure Automation Framework."""

import yaml
from pathlib import Path
from typing import Any
from model.errors import ModelParseError
from observability import get_logger

logger = get_logger(__name__)


def parse_yaml(file_path: Path) -> Any:
    """Parse a YAML file into Python objects.

    Args:
        file_path: Path to the YAML file to parse

    Returns:
        Parsed Python object from the YAML file

    Raises:
        ModelParseError: If YAML syntax is invalid
    """
    logger.info("Starting to parse YAML file: %s", file_path)
    
    try:
        with file_path.open("r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as error:
        logger.error("Failed to parse YAML file %s: %s", file_path, str(error))
        raise ModelParseError(f"Invalid YAML syntax in {file_path}: {str(error)}") from error