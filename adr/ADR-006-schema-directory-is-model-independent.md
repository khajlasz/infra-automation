# ADR-006: Make the Schema Model-Independent

**Status:** Accepted

## Context

The project originally contained a single reference model (`telecom`), therefore the schema was organized as:

```text
schema/
    telecom/
        application/
        compute/
        network/
        platform/
```

The project has since evolved to support multiple reference models:

```text
models/
    telecom/
    out-dialer/
```

Both models are validated using the same schema. The schema describes the generic Platform Model rather than any individual reference model.

Keeping the schema under `schema/telecom/` incorrectly suggests that the schema is specific to the telecom example, even though it is shared by all current and future reference models.

## Decision

The schema SHALL become model-independent.

The directory structure SHALL be:

```text
schema/
    application/
    compute/
    network/
    platform/
```

Reference models SHALL remain organized independently under:

```text
models/
    telecom/
    out-dialer/
    ...
```

Validation SHALL always use the common schema directory regardless of which reference model is being validated.

Examples:

```text
models/telecom
        │
        ▼
     schema/
```

```text
models/out-dialer
        │
        ▼
     schema/
```

Both reference models SHALL be validated against the same Platform Model schema.

## Consequences

### Advantages

- Removes misleading telecom-specific naming.
- Clearly separates the Platform Model definition from reference implementations.
- Simplifies validation by using a single schema root.
- Makes it straightforward to introduce additional reference models.
- Better reflects the architecture of the Infrastructure Automation Framework.

### Disadvantages

This change requires a small refactoring of:

- validation module
- CLI
- tests
- documentation
- any hard-coded schema paths

No functional changes are expected.

## Rationale

The schema defines the contract of the Platform Model.

Reference models are example implementations that conform to this contract.

Therefore, the schema belongs to the framework itself rather than to any individual reference model.