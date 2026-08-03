"""Framework exceptions for model loading."""


class ModelError(Exception):
    """Raised when model files do not follow framework conventions."""


class ModelParseError(ModelError):
    """Raised when YAML parsing fails."""
