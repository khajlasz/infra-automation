"""Command-line entry point for Infrastructure Automation."""

import argparse
from pathlib import Path

from validation import validate_model_schema, validate_model
from generators.docker_compose import DockerComposeGenerator
from loader.loader import Loader
from observability.logger import get_logger

from generators.terraform_routeros import TerraformRouterOSGenerator
from realization import load_realization

logger = get_logger(__name__)


def generate_docker_compose(
    model_directory: Path,
    output: Path,
    realization_path: Path | None = None,
) -> None:
    """Generate Docker Compose specification from a platform model."""
    loader = Loader()
    model = loader.load(model_directory)

    realization = (
        load_realization(realization_path)
        if realization_path is not None
        else None
    )

    generator = DockerComposeGenerator()
    compose_spec = generator.generate(model, realization)

    yaml_output = generator.serialize(compose_spec)

    output.write_text(
        yaml_output,
        encoding="utf-8",
    )

    logger.info(
        "Docker Compose specification written to %s",
        output,
    )

def generate_terraform_routeros(
    model_directory: Path,
    realization_path: Path,
    output: Path,
) -> None:
    """Generate RouterOS Terraform configuration."""

    loader = Loader()
    model = loader.load(model_directory)
    realization = load_realization(realization_path)

    generator = TerraformRouterOSGenerator()
    terraform_spec = generator.generate(model, realization)
    hcl_output = generator.serialize(terraform_spec)

    output.write_text(
        hcl_output,
        encoding="utf-8",
    )

    logger.info(
        "RouterOS Terraform configuration written to %s",
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

    compose_command.add_argument(
        "--realization",
        type=Path,
        help="Optional deployment realization file.",
    )

    terraform_command = generate_subcommands.add_parser(
        "terraform-routeros",
        help="Generate RouterOS Terraform configuration.",
    )
    terraform_command.add_argument(
        "model_directory",
        type=Path,
        help="Path to the platform model directory.",
    )
    terraform_command.add_argument(
        "--realization",
        type=Path,
        required=True,
        help="Path to the deployment realization file.",
    )
    terraform_command.add_argument(
        "--output",
        type=Path,
        default=Path("generated.tf"),
        help="Output file path (default: generated.tf)",
    )
    arguments = parser.parse_args()
    if arguments.command == "validate":
        schema_directory = Path(__file__).parents[1] / "schema"
        validate_model_schema(arguments.model_directory, schema_directory)
        validate_model(arguments.model_directory)
        
    elif arguments.command == "generate":
        if arguments.generate_command == "docker-compose":
            generate_docker_compose(
                arguments.model_directory,
                arguments.output,
                arguments.realization,
            )

        elif arguments.generate_command == "terraform-routeros":
            generate_terraform_routeros(
                arguments.model_directory,
                arguments.realization,
                arguments.output,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
