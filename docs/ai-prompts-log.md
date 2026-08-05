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

------------------

Task

Update the YAML schema files so that BOTH reference models validate successfully:

- models/telecom
- models/out-dialer

The architecture and information model have already been decided.
Do NOT redesign the model or the schema.
If you think an architectural change is needed, describe it in the summary instead of implementing it.

====================================================
PHASE 1 – COMPLETE IMPACT ANALYSIS (NO CHANGES YET)
====================================================

There are 11 schema files under schema/telecom/.

Inspect EVERY schema file.

For EACH schema file:

1. Read the schema file.
2. Read the corresponding file from models/telecom/.
3. Read the corresponding file from models/out-dialer/.
4. Compare the structures.
5. Decide whether the schema requires changes.

Before editing anything, produce a checklist like this:

[ ] platform/platform.yaml
    Needs update: YES/NO
    Reason:

[ ] application/applications.yaml
    Needs update: YES/NO
    Reason:

...

Repeat for ALL schema files.

Do NOT begin implementation until all schema files have been inspected.

====================================================
PHASE 2 – IMPLEMENTATION
====================================================

Update ONLY the schema files marked "Needs update: YES".

Requirements:

- Preserve the existing schema structure.
- Preserve the existing validation philosophy.
- Make the minimum necessary changes.
- Keep full backwards compatibility with the telecom model.
- Add support only for fields that already exist in the out-dialer model.
- Do NOT modify either reference model.
- Do NOT rename schema files.
- Do NOT remove validation for telecom fields unless those fields have been removed from BOTH reference models.

====================================================
PHASE 3 – VALIDATION
====================================================

Run the schema validation tests.

If validation cannot be executed because the Python environment is unavailable,
clearly explain why and provide the exact command that should be executed.

====================================================
DELIVERABLES
====================================================

Provide:

1. The completed inspection checklist.
2. The list of modified schema files.
3. For each modified file:
   - what changed,
   - why it was necessary,
   - which field(s) from the out-dialer model required the change.
4. Validation results.
5. Any concerns or architectural observations (do NOT implement them).

----------------------

Task

Update the YAML schema files so that BOTH reference models validate successfully:

- models/telecom
- models/out-dialer

The architecture and information model have already been decided.

Do NOT redesign the architecture or the schema.
Do NOT modify either reference model.

If you believe an architectural change is required, describe it in the final summary instead of implementing it.

====================================================
PROCESS THE SCHEMA ONE FILE AT A TIME
====================================================

There are 11 schema files under schema/telecom/.

Process them sequentially.

For EACH schema file:

1. Read the schema file.

2. Read ONLY the corresponding telecom model file.

3. Read ONLY the corresponding out-dialer model file.

4. Compare the structures.

5. Decide whether this schema file requires changes.

6. If changes are required:
   - update ONLY this schema file
   - make the minimum necessary changes
   - preserve backwards compatibility with the telecom model

7. Print a short summary:

   Processing:
   <schema file>

   Updated:
   YES / NO

   Reason:
   ...

8. Continue to the next schema file.

IMPORTANT:

Do NOT read all schema files before starting implementation.

Do NOT compare the entire project first.

Complete one schema file before moving to the next.

Treat every schema file as an independent task.

====================================================
RULES
====================================================

- Preserve the existing schema structure.
- Preserve the existing validation philosophy.
- Make the minimum necessary changes.
- Keep full backwards compatibility with the telecom model.
- Add support only for fields that already exist in the out-dialer model.
- Do NOT redesign the schema.
- Do NOT remove telecom support unless the corresponding field has been removed from BOTH reference models.

====================================================
VALIDATION
====================================================

After processing all schema files:

- run the schema validation tests

If the Python environment is unavailable, explain why and provide the exact command that should be executed.

====================================================
FINAL SUMMARY
====================================================

Provide:

- list of modified schema files
- explanation of every change
- validation results
- any architectural concerns (do NOT implement them)