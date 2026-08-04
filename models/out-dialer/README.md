# Telecom Reference Model

## Purpose

The telecom model is the first reference implementation of the Infrastructure
Automation Framework.

It is inspired by Cisco BroadWorks deployments, but is intentionally modelled
using generic infrastructure concepts wherever possible.

The objective is to demonstrate modelling of a complex distributed platform,
including:

- multiple sites,
- network automation,
- compute infrastructure,
- software deployments,
- declarative configuration.

BroadWorks terminology is retained only where it helps explain real deployment
patterns. The long-term goal is to progressively replace product-specific
concepts with generic modelling constructs without losing architectural realism.

```
model/
└── telecom/
    ├── README.md
    ├── platform/
    ├── network/
    ├── compute/
    └── application/
```

## Why Telecom?

Telecommunications platforms are excellent examples of complex distributed
systems.

They include:

- multiple network zones,
- stateful and stateless services,
- management networks,
- high availability,
- deployment dependencies,
- strict security boundaries.

These characteristics make them a realistic domain for developing a generic
platform modelling framework.

**NOTE:
This model is intentionally not a representation of Cisco BroadWorks internals. It is a learning and demonstration model inspired by production deployment experience. Product names are used only where they help explain deployment patterns and architectural relationships.**