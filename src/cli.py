"""Command-line entry point for Infrastructure Automation."""

import argparse
from pathlib import Path

from validation import validate_model_schema, validate_model
from generators.docker_compose import DockerComposeGenerator
from loader.loader import Loader
from observability.logger import get_logger


logger = get_logger(__name__)


def generate_docker_compose(
    model_directory: Path,
    output: Path,
) -> None:
    """Generate Docker Compose specification from a platform model."""
    # Load the platform model
    loader = Loader()
    model = loader.load(model_directory)
    
    # Generate Docker Compose specification
    generator = DockerComposeGenerator()
    compose_spec = generator.generate(model)
    
    # Serialize to YAML
    yaml_output = generator.serialize(compose_spec)
    
    # Write to file with explicit UTF-8 encoding
    output.write_text(
        yaml_output,
        encoding="utf-8",
    )
    
    logger.info(
        "Docker Compose specification written to %s",
        output,
    )


def main() -> int:
    """Run the initial command-line interface."""
    parser = argparse.ArgumentParser(
        description="Infrastructure Automation Framework"
    )
    commands = parser.add_subparsers(dest="command")
    commands.required = True
    validate_command = commands.add_parser(
        "validate", help="Validate a model against its Yamale schemas."
    )
    validate_command.add_argument(
        "model_directory",
        type=Path,
        help="Path to the model directory to validate.",
    )
    
    # Add generate docker-compose command
    generate_command = commands.add_parser(
        "generate",
        help="Generate Docker Compose specifications from a platform model."
    )
    generate_subcommands = generate_command.add_subparsers(dest="generate_command")
    generate_subcommands.required = True
    
    compose_command = generate_subcommands.add_parser(
        "docker-compose",
        help="Generate Docker Compose specification."
    )
    compose_command.add_argument(
        "model_directory",
        type=Path,
        help="Path to the model directory to generate Docker Compose for.",
    )
    compose_command.add_argument(
        "--output",
        type=Path,
        default=Path("docker-compose.yaml"),
        help="Output file path (default: docker-compose.yaml)",
    )

    arguments = parser.parse_args()
    if arguments.command == "validate":
        schema_directory = Path(__file__).parents[1] / "schema"
        validate_model_schema(arguments.model_directory, schema_directory)
        validate_model(arguments.model_directory)
        
    elif arguments.command == "generate" and arguments.generate_command == "docker-compose":
        generate_docker_compose(arguments.model_directory, arguments.output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
