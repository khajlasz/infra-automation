Task

Update the YAML schema files under schema/ so that they validate BOTH reference models:

- models/telecom
- models/out-dialer

Requirements

- Preserve the existing schema structure and validation philosophy.
- Make the minimum necessary changes.
- Do not redesign or simplify the schema.
- Do not modify either reference model.
- Keep backwards compatibility with the telecom model.
- Add support only for fields that exist in the Out-Dialer model.

Validation

After the changes:

- models/telecom must validate successfully.
- models/out-dialer must validate successfully.
- Existing schema tests must continue to pass.

Deliverables

- Updated schema files only.
- A short explanation describing:
  - which schema files were modified,
  - which new fields were introduced,
  - why each change was necessary.

Do not remove support for any field used by the telecom model unless the same
field has already been removed from both reference models.

Before making any changes:

1. Compare the telecom and out-dialer models.
2. Identify every schema mismatch.
3. Update only the affected schema files.

Assume all architectural decisions have already been made.

If you think the architecture should change, do not implement the change.
Instead, explain your concern in the summary.