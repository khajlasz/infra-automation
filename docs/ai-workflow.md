# AI-Assisted Development Workflow

This project uses AI as an engineering assistant, not as an architectural source
of truth.

Architectural decisions are discussed explicitly, documented in ADRs and
reviewed before implementation. AI-assisted coding is used primarily for
implementation, repository analysis, repetitive refactoring and test support.

## Workflow

A typical change follows this pattern:

```text
Engineering question
        │
        ▼
Architecture / design decision
        │
        ▼
Scoped implementation prompt
        │
        ▼
AI-assisted implementation
        │
        ▼
Human review
        │
        ▼
Tests / validation
        │
        ▼
Commit
```

Prompts are intentionally constrained. They normally identify:

- the requested task,
- relevant files and architecture,
- constraints that must be preserved,
- changes that are explicitly out of scope,
- validation that must be run,
- expected deliverables.

The project favours small, reviewable changes rather than asking an AI model to
redesign large parts of the repository autonomously.

## Local AI Workflow

Local coding assistance can be provided through Ollama and OpenCode. This keeps
routine repository analysis and implementation close to the development
environment while allowing architecture and design decisions to remain an
explicit engineering activity.

The specific model or assistant is not part of the framework architecture and
can be replaced without affecting the project.

## Repository Guidance

`AGENTS.md` contains the engineering rules supplied to AI agents and human
contributors. In particular:

- preserve architectural decisions,
- make the smallest necessary change,
- do not silently redesign the Platform Model,
- prefer simplicity before abstraction,
- validate changes before declaring work complete.

Detailed raw prompt/session logs are development working material rather than a
required part of the public project documentation.
