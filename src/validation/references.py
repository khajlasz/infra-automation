"""Cross-file reference validation.

Reference validation belongs in the framework rather than Yamale schemas.
It will be implemented after the model loader can assemble a complete model.
"""

from pathlib import Path


def validate_references(model_directory: Path) -> None:
    """Validate references between model files.

    The initial framework intentionally does not implement cross-file checks.
    """
    raise NotImplementedError(
        f"Reference validation is not implemented for {model_directory}"
    )
