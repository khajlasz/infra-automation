from pathlib import Path

from validation.schema import validate_realization_schema

def test_local_lab_realization_validates():
    validate_realization_schema(
        Path("realizations/out-dialer/local-lab.yaml"),
        Path("schema/realizations/realization.yaml"),
    )