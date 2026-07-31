"""Tests for recursive Yamale schema validation."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from validation import validate_model_schema


class ModelSchemaValidationTests(unittest.TestCase):
    def test_validates_every_file_in_the_minimal_model(self) -> None:
        repository_root = Path(__file__).parents[1]

        validate_model_schema(
            repository_root / "models" / "minimal",
            repository_root / "schema" / "telecom",
        )
