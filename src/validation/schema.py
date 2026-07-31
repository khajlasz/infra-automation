"""Validate model files against Yamale schemas."""

from pathlib import Path

import yamale

from model.discovery import discover_yaml_files
from observability import get_logger


logger = get_logger(__name__)


def validate_schema(model_path: Path, schema_path: Path) -> None:
    """Validate one model file using its Yamale schema."""
    schema = yamale.make_schema(str(schema_path))
    data = yamale.make_data(str(model_path))
    yamale.validate(schema, data)


def validate_model_schema(model_directory: Path, schema_directory: Path) -> None:
    """Validate every model YAML file against its corresponding schema."""
    logger.info("Validating schema for model %s", model_directory)
    validated_file_count = 0

    for model_path, relative_path in discover_yaml_files(model_directory):
        schema_path = schema_directory / relative_path
        logger.info("Validating model file %s", relative_path)
        try:
            validate_schema(model_path, schema_path)
        except yamale.YamaleError as error:
            logger.error("Schema validation failed for %s", relative_path)
            logger.error("Error: %s", error)
            raise

        validated_file_count += 1

    logger.info("Successfully validated %s model files", validated_file_count)
