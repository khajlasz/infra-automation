"""Validate model files against Yamale schemas."""

from pathlib import Path

import yamale


def validate_schema(model_path: Path, schema_path: Path) -> None:
    """Validate one model file using its Yamale schema."""
    schema = yamale.make_schema(str(schema_path))
    data = yamale.make_data(str(model_path))
    yamale.validate(schema, data)
