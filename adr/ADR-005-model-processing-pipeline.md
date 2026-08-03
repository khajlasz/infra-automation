# ADR-005: Model Processing Pipeline

## Status

Accepted

---

## Context

Infrastructure models are processed through several distinct stages.

Each stage has a single responsibility.

Separating responsibilities simplifies testing, improves observability and
prevents duplication of validation logic.

---

## Decision

The Infrastructure Automation Framework SHALL process models using the
following pipeline.

```
Model Discovery
        │
        ▼
YAML Parsing
        │
        ▼
Schema Validation
        │
        ▼
Platform Model Loading
        │
        ▼
Framework Validation
        │
        ▼
Output Generation
```

The stages exchange well-defined inputs and outputs.

| Stage | Input | Output |
|--------|-------|--------|
| Model Discovery | Model directory | Ordered collection of model YAML files |
| YAML Parsing | Model YAML files | Parsed Python objects (`dict`, `list`, `str`, ...) |
| Schema Validation | Parsed model data + Yamale schemas | Schema-validated model data |
| Platform Model Loading | Schema-validated model data | `PlatformModel` |
| Framework Validation | `PlatformModel` | Validated `PlatformModel` |
| Output Generation | Validated `PlatformModel` | Terraform, Ansible, NetBox, ... |

---

## Stage Responsibilities

### Model Discovery

Discover all model files that belong to a platform model.

Responsibilities:

- discover model files
- preserve deterministic processing order

---

### YAML Parsing

Validate that every model file is valid YAML.

Responsibilities:

- parse YAML
- report syntax errors
- identify the offending file
- stop processing on failure

This stage SHALL NOT perform schema or semantic validation.

---

### Schema Validation

Validate individual model files using Yamale schemas.

Responsibilities:

- required fields
- data types
- regular expressions
- structural validation

This stage SHALL NOT validate relationships between model objects.

---

### Platform Model Loading

Build the in-memory `PlatformModel`.

Responsibilities:

- transform schema-validated model data into domain objects
- assemble the complete platform model
- preserve model hierarchy
- expose a consistent object model

This stage assumes successful YAML parsing and schema validation.

The loader SHALL NOT perform syntax, schema or semantic validation.

---

### Framework Validation

Validate semantic relationships within the assembled `PlatformModel`.

Examples include:

- reference integrity
- uniqueness
- consistency
- policy validation

Validation rules are specified in:

```
docs/validation-registry.md
```

---

### Output Generation

Generate infrastructure artefacts.

Examples:

- Terraform
- Ansible
- NetBox

Generation assumes a valid `PlatformModel`.

---

## Consequences

### Advantages

- Clear separation of responsibilities.
- Explicit data flow between stages.
- Simpler testing.
- Better observability.
- Independent evolution of each stage.
- No duplicated validation logic.

### Trade-offs

- Additional pipeline stage.
- More explicit orchestration in the CLI.