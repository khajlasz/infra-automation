"""Milestone 1 contracts; no Kubernetes generation or live cluster access."""
from pathlib import Path

import pytest
import yaml
import yamale

from loader import Loader
from model import ModelError
from realization import load_realization
from validation.framework import validate_realization_references
from validation.schema import validate_realization_schema, validate_schema


REALIZATION = Path("realizations/out-dialer/local-lab.yaml")
REALIZATION_SCHEMA = Path("schema/realizations/realization.yaml")


@pytest.fixture
def inputs():
    return Loader().load(Path("models/out-dialer")), load_realization(REALIZATION)


def test_model_and_realization_contract(inputs):
    model, realization = inputs
    assert model.compute.compute_profiles == {
        "small": {"cpu": 0.25, "ram": 256},
        "medium": {"cpu": 0.5, "ram": 512},
        "large": {"cpu": 1, "ram": 1024},
    }
    apps = model.application.applications
    assert apps["Portal"]["endpoints"]["http"] == {"protocol": "HTTP", "port": 8443}
    assert "https" not in apps["Portal"]["endpoints"]
    assert apps["Authentication"]["endpoints"]["https"]["protocol"] == "HTTPS"
    for name in ("Portal", "CampaignManager", "CallSimulator"):
        assert apps[name]["endpoints"]["metrics"]["path"] == "/metrics"
    assert realization.kubernetes == yaml.safe_load(REALIZATION.read_text())["kubernetes"]
    assert realization.kubernetes["namespace"] == "out-dialer"
    assert realization.kubernetes["workloads"] == {"portal": {
        "replicas": 2,
        "imagePullPolicy": "Never",
        "endpoints": {"http": {"application": "Portal", "endpoint": "http"}},
        "service": {"type": "ClusterIP"},
        "probes": {
            "readiness": {"path": "/health", "port": "http",
                          "initialDelaySeconds": 3, "periodSeconds": 5},
            "liveness": {"path": "/health", "port": "http",
                         "initialDelaySeconds": 10, "periodSeconds": 10},
        },
    }}
    assert realization.kubernetes["observability"] == {"metrics": {
        "externalInterface": "metrics", "discovery": "prometheus-annotations"}}
    assert "node" not in realization.kubernetes["workloads"]["portal"]
    validate_realization_schema(REALIZATION, REALIZATION_SCHEMA)
    validate_realization_references(model, realization)


def test_legacy_realization_remains_optional(tmp_path, inputs):
    model, _ = inputs
    path = tmp_path / "legacy.yaml"
    path.write_text("name: legacy\n")
    validate_realization_schema(path, REALIZATION_SCHEMA)
    realization = load_realization(path)
    assert realization.kubernetes == {}
    validate_realization_references(model, realization)


@pytest.mark.parametrize("case, message", [
    ("node", "REF-010:.*unknown compute node 'missing'"),
    ("deployment", "REF-011:.*unknown deployment"),
    ("application", "REF-011:.*unknown or uninstalled application"),
    ("uninstalled", "REF-011:.*unknown or uninstalled application"),
    ("endpoint", "REF-011:.*unknown endpoint 'missing'"),
    ("duplicate", "REF-011:.*duplicate endpoint"),
    ("protocol", "REF-011:.*unsupported protocol"),
    ("probe", "REF-011:.*unknown selected port"),
    ("probe_protocol", "REF-011:.*requires an HTTP/HTTPS endpoint"),
    ("interface", "REF-012:.*unknown external interface"),
    ("ambiguous_metrics", "REF-012:.*found 2"),
    ("metrics_endpoint", "REF-012:.*valid HTTP metrics endpoint"),
    ("metrics_path", "REF-012:.*valid HTTP metrics endpoint"),
    ("metrics_protocol", "REF-012:.*valid HTTP metrics endpoint"),
])
def test_invalid_references_rejected(inputs, case, message):
    model, realization = inputs
    kube = realization.kubernetes
    workload = kube["workloads"]["portal"]
    binding = workload["endpoints"]["http"]
    targets = model.platform.external_interfaces["metrics"]["targets"]
    portal = model.application.applications["Portal"]["endpoints"]
    if case == "node":
        kube["workloads"]["missing"] = kube["workloads"].pop("portal")
    elif case == "deployment":
        model.compute.nodes["portal"]["deployment"] = "missing"
    elif case == "application":
        binding["application"] = "missing"
    elif case == "uninstalled":
        binding.update(application="CampaignManager", endpoint="rest")
    elif case == "endpoint":
        binding["endpoint"] = "missing"
    elif case == "duplicate":
        workload["endpoints"]["other"] = dict(binding)
    elif case == "protocol":
        portal["http"]["protocol"] = "SCTP"
    elif case == "probe":
        workload["probes"]["readiness"]["port"] = "missing"
    elif case == "probe_protocol":
        portal["http"]["protocol"] = "TCP"
    elif case == "interface":
        kube["observability"]["metrics"]["externalInterface"] = "missing"
    elif case == "ambiguous_metrics":
        targets.append(dict(targets[0]))
    elif case == "metrics_endpoint":
        targets[0]["endpoint"] = "missing"
    elif case == "metrics_path":
        portal["metrics"].pop("path")
    elif case == "metrics_protocol":
        portal["metrics"]["protocol"] = "TCP"
    with pytest.raises(ModelError, match=message):
        validate_realization_references(model, realization)


@pytest.mark.parametrize("field,value", [
    ("node", "portal"), ("replicas", 0), ("imagePullPolicy", "Sometimes"),
    ("service", {"type": "Invalid"}),
    ("probes", {"readiness": {"path": "health", "port": "http",
                             "initialDelaySeconds": 0, "periodSeconds": 5}}),
])
def test_invalid_realization_schema(tmp_path, field, value):
    data = yaml.safe_load(REALIZATION.read_text())
    data["kubernetes"]["workloads"]["portal"][field] = value
    path = tmp_path / "invalid.yaml"
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(yamale.YamaleError):
        validate_realization_schema(path, REALIZATION_SCHEMA)


@pytest.mark.parametrize("cpu,ram,valid", [
    (0.25, 256, True), (0.5, 512, True), (1, 1024, True), (4, 8192, True),
    (0, 256, False), (-0.1, 256, False), (True, 256, False),
    (float("inf"), 256, False), (float("nan"), 256, False),
    (0.25, 0, False), (0.25, 1.5, False),
])
def test_compute_profile_schema(tmp_path, cpu, ram, valid):
    path = tmp_path / "profiles.yaml"
    path.write_text(yaml.safe_dump({"compute_profiles": {"test": {"cpu": cpu, "ram": ram}}}))
    if valid:
        validate_schema(path, Path("schema/compute/compute-profiles.yaml"))
    else:
        with pytest.raises(yamale.YamaleError):
            validate_schema(path, Path("schema/compute/compute-profiles.yaml"))


@pytest.mark.parametrize("path_value,valid", [(None, True), ("/metrics", True), ("metrics", False)])
def test_endpoint_path_schema(tmp_path, path_value, valid):
    endpoint = {"protocol": "HTTP", "port": 9090}
    if path_value is not None:
        endpoint["path"] = path_value
    path = tmp_path / "applications.yaml"
    path.write_text(yaml.safe_dump({"applications": {"Test": {
        "description": "Test", "endpoints": {"metrics": endpoint}}}}))
    if valid:
        validate_schema(path, Path("schema/application/applications.yaml"))
    else:
        with pytest.raises(yamale.YamaleError):
            validate_schema(path, Path("schema/application/applications.yaml"))


@pytest.mark.parametrize("matching", [False, True])
def test_ref_012_allows_zero_or_one_matching_target(inputs, matching):
    model, realization = inputs
    if not matching:
        model.platform.external_interfaces["metrics"]["targets"].pop(0)
    validate_realization_references(model, realization)


def test_ref_012_rejects_distinct_ambiguous_targets(inputs):
    model, realization = inputs
    model.application.deployments["portal"]["applications"].append(
        {"application": "CampaignManager"})
    with pytest.raises(ModelError, match=(
        r"REF-012:.*workload 'portal'.*ambiguous metrics targets.*"
        r"Portal.metrics, CampaignManager.metrics")):
        validate_realization_references(model, realization)


@pytest.mark.parametrize("case", [
    "application", "endpoint", "path", "protocol", "network", "missing_application",
    "missing_endpoint", "missing_network", "malformed", "source", "missing_source",
    "missing_targets",
])
def test_ref_012_validates_metadata_before_workload_filtering(inputs, case):
    model, realization = inputs
    interface = model.platform.external_interfaces["metrics"]
    # Portal has no matching target, but invalid targets must still fail.
    interface["targets"].pop(0)
    target = interface["targets"][0]
    endpoint = model.application.applications["CampaignManager"]["endpoints"]["metrics"]
    if case in {"application", "endpoint", "network"}:
        target[case] = "missing"
    elif case in {"missing_application", "missing_endpoint", "missing_network"}:
        target.pop(case.removeprefix("missing_"))
    elif case == "path":
        endpoint.pop("path")
    elif case == "protocol":
        endpoint["protocol"] = "TCP"
    elif case == "malformed":
        interface["targets"][0] = "invalid"
    elif case == "source":
        interface["sourceNetwork"] = "missing"
    elif case == "missing_source":
        interface.pop("sourceNetwork")
    elif case == "missing_targets":
        interface.pop("targets")
    with pytest.raises(ModelError, match="REF-012:"):
        validate_realization_references(model, realization)


@pytest.mark.parametrize("port", [8443, 8444])
def test_ref_011_selected_numeric_ports_must_be_unique(inputs, port):
    model, realization = inputs
    model.application.applications["Authentication"]["endpoints"]["https"]["port"] = port
    realization.kubernetes["workloads"]["portal"]["endpoints"]["secondary"] = {
        "application": "Authentication", "endpoint": "https"}
    if port == 8443:
        with pytest.raises(ModelError, match=(
            r"REF-011:.*workload 'portal'.*container port 8443.*"
            r"Portal.http.*Authentication.https")):
            validate_realization_references(model, realization)
    else:
        validate_realization_references(model, realization)
