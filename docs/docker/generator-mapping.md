# Docker Compose Generator Mapping

This document specifies how Platform Model objects are transformed into
Docker Compose artifacts.

The mapping is deterministic: every generated field is derived from the
Platform Model or from a documented generator transformation. The
generator must not infer or invent information that is not represented
in the Platform Model.

| Docker Compose    | Platform Model Source  | Generator Transformation |
| ----------------- | ---------------------- | ------------------------ |
| `services.<name>` | `compute.nodes.<node>` | snake_case → kebab-case  |
| `image`        | `compute.nodes.<node>.deployment.product`                        | `<vendor>/<edition>:<version>`                           |
| `hostname`     | `compute.nodes.<node>`                      | copy node name                                            |
| `networks`     | `compute.nodes.<node>.interfaces.*.network` | collect unique network names                                     |
| `ports`        | `compute.nodes.<node>.deployment.applications[*].endpoints`      | emit one published port per endpoint |



