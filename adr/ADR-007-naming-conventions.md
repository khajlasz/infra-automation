## Naming Conventions

The Platform Model uses snake_case identifiers for deployments and nodes.

Deployment generators translate identifiers to technology-specific naming conventions.

Examples:

- Docker Compose: snake_case → kebab-case
- Kubernetes: snake_case → kebab-case
- Terraform resource names: snake_case
- Python objects: snake_case

Application names remain PascalCase because they represent logical software components rather than runtime identifiers.