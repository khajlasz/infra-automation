"""Command-line entry point for Infrastructure Automation."""

import argparse
from pathlib import Path

from validation import validate_model_schema, validate_model


def main() -> int:
    """Run the initial command-line interface."""
    parser = argparse.ArgumentParser(
        description="Infrastructure Automation Framework"
    )
    commands = parser.add_subparsers(dest="command")
    validate_command = commands.add_parser(
        "validate", help="Validate a model against its Yamale schemas."
    )
    validate_command.add_argument(
        "model_directory",
        type=Path,
        help="Path to the model directory to validate.",
    )

    arguments = parser.parse_args()
    if arguments.command == "validate":
        schema_directory = Path(__file__).parents[1] / "schema"
        validate_model_schema(arguments.model_directory, schema_directory)
        validate_model(arguments.model_directory)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
