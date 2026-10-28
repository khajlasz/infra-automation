"""Capacity sizing independent of compute-node placement."""
from pathlib import Path
import subprocess
import sys

import pytest

from loader import Loader
from model import ModelError
from realization import load_realization
from realization.resources import resolve_kubernetes_requests
from validation.framework import validate_realization_references


@pytest.mark.parametrize("profile,cpu,memory", [
    ("small", 500, 512), ("medium", 1000, 1024), ("large", 2000, 2048)])
@pytest.mark.parametrize("replicas", [1, 2, 3])
def test_capacity_reference_table(profile, cpu, memory, replicas):
    model = Loader().load(Path("models/out-dialer"))
    resources = resolve_kubernetes_requests(model.compute.compute_profiles[profile], replicas)
    assert resources == {"requests": {
        "cpu": f"{cpu // replicas}m", "memory": f"{memory // replicas}Mi"}}
    assert "limits" not in resources
    assert resources == resolve_kubernetes_requests(model.compute.compute_profiles[profile], replicas)
    # Flooring never overspends the fixed total budget.
    assert (cpu // replicas) * replicas <= cpu
    assert (memory // replicas) * replicas <= memory


@pytest.mark.parametrize("replicas", [0, -1, 1.5, True, "2", None])
def test_invalid_replicas(replicas):
    with pytest.raises(ModelError, match="positive integer"):
        resolve_kubernetes_requests({"cpu": 1, "ram": 1024}, replicas)


@pytest.mark.parametrize("profile", [
    {"cpu": 0, "ram": 1024}, {"cpu": -1, "ram": 1024},
    {"cpu": float("inf"), "ram": 1024}, {"cpu": True, "ram": 1024},
    {"cpu": 1, "ram": 0}, {"cpu": 1, "ram": -1}, {"cpu": 1, "ram": 1.5},
    {}, {"cpu": 0.001, "ram": 1024}, {"cpu": 1, "ram": 1},
])
def test_invalid_capacity(profile):
    with pytest.raises(ModelError):
        resolve_kubernetes_requests(profile, 2)


def test_decimal_cpu_has_no_float_artifacts():
    assert resolve_kubernetes_requests({"cpu": 0.3, "ram": 1024}, 3) == {
        "requests": {"cpu": "50m", "memory": "170Mi"}}


@pytest.mark.parametrize("profile", [None, "missing"])
def test_profile_reference_required(profile):
    model = Loader().load(Path("models/out-dialer"))
    realization = load_realization(Path("realizations/out-dialer/local-lab.yaml"))
    realization.kubernetes["workloads"]["portal"]["computeProfile"] = profile
    with pytest.raises(ModelError, match="REF-010:.*unknown compute profile"):
        validate_realization_references(model, realization)


def test_workload_bypasses_compute_nodes():
    model = Loader().load(Path("models/out-dialer"))
    realization = load_realization(Path("realizations/out-dialer/local-lab.yaml"))
    realization.docker = {}
    model.compute.nodes.clear()
    workload = realization.kubernetes["workloads"].pop("portal")
    realization.kubernetes["workloads"]["portal-app"] = workload
    validate_realization_references(model, realization)
    assert resolve_kubernetes_requests(
        model.compute.compute_profiles[workload["computeProfile"]], workload["replicas"]
    ) == {"requests": {"cpu": "250m", "memory": "256Mi"}}


def test_cli_validates_realization():
    result = subprocess.run([
        sys.executable, "src/cli.py", "validate", "models/out-dialer",
        "--realization", "realizations/out-dialer/local-lab.yaml",
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("replicas", [0, -1, 1.5, True])
def test_semantic_validation_rejects_invalid_replicas(replicas):
    model = Loader().load(Path("models/out-dialer"))
    realization = load_realization(Path("realizations/out-dialer/local-lab.yaml"))
    realization.kubernetes["workloads"]["portal"]["replicas"] = replicas
    with pytest.raises(ModelError, match="REF-010:.*positive integer"):
        validate_realization_references(model, realization)


@pytest.mark.parametrize("case", ["missing_profile", "unknown_profile", "zero_replicas", "fractional_replicas"])
def test_cli_rejects_invalid_sizing(tmp_path, case):
    import yaml

    data = yaml.safe_load(Path("realizations/out-dialer/local-lab.yaml").read_text())
    workload = data["kubernetes"]["workloads"]["portal"]
    if case == "missing_profile":
        workload.pop("computeProfile")
    elif case == "unknown_profile":
        workload["computeProfile"] = "missing"
    else:
        workload["replicas"] = 0 if case == "zero_replicas" else 1.5
    path = tmp_path / "invalid.yaml"
    path.write_text(yaml.safe_dump(data))
    result = subprocess.run([
        sys.executable, "src/cli.py", "validate", "models/out-dialer",
        "--realization", str(path),
    ], capture_output=True, text=True)
    assert result.returncode != 0
    assert ("REF-010:" if case == "unknown_profile" else "YamaleError") in result.stderr
