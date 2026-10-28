"""Resolve Kubernetes requests from logical workload capacity budgets."""

import math
from fractions import Fraction

from model import ModelError


def resolve_kubernetes_requests(profile, replicas):
    """Allocate half the capacity equally, flooring to whole millicores and MiB."""
    if type(replicas) is not int or replicas <= 0:
        raise ModelError("Kubernetes replicas must be a positive integer")
    cpu, ram = profile.get("cpu"), profile.get("ram")
    if (isinstance(cpu, bool) or not isinstance(cpu, (int, float))
            or not math.isfinite(cpu) or cpu <= 0):
        raise ModelError("Kubernetes profile CPU capacity must be positive and finite")
    if type(ram) is not int or ram <= 0:
        raise ModelError("Kubernetes profile RAM capacity must be a positive integer MiB")
    # Fraction preserves the model's decimal value without binary float artifacts.
    millicores = Fraction(str(cpu)) * 1000 // (2 * replicas)
    memory = ram // (2 * replicas)
    if millicores < 1 or memory < 1:
        raise ModelError("Kubernetes requests round below 1m CPU or 1Mi memory")
    return {"requests": {"cpu": f"{millicores}m", "memory": f"{memory}Mi"}}
