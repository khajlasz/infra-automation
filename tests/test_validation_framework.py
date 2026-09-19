"""Tests for semantic model validation."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from loader import Loader
from model import ModelError
from validation import validate_model
from realization import load_realization
from src.validation.framework import (
    _validate_ref_001,
    _validate_ref_002,
    _validate_ref_003,
    _validate_ref_004,
    _validate_ref_005,
    _validate_ref_006,
    _validate_ref_007,
    _validate_ref_008,
    _validate_ref_009,
    validate_realization_references,

)


class SemanticValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).parents[1]
        self.minimal_model_directory = self.repo_root / "models" / "minimal"
        self.out_dialer_model_directory = self.repo_root / "models" / "out-dialer"
        self.out_dialer_realization = (
            self.repo_root
            / "realizations"
            / "out-dialer"
            / "local-lab.yaml"
        )

    def test_validates_model_with_correct_references(self) -> None:
        """Test that a valid model passes semantic validation."""
        validate_model(self.out_dialer_model_directory)

    def test_ref_001_rejects_unknown_site(self) -> None:
        model = Loader().load(self.minimal_model_directory)

        node = next(iter(model.compute.nodes.values()))
        node["site"] = "unknown-site"

        with self.assertRaisesRegex(
            ModelError,
            r"REF-001: Node '.+' references unknown site 'unknown-site'",
        ):
            _validate_ref_001(model)

    def test_ref_002_rejects_unknown_network(self) -> None:
        model = Loader().load(self.out_dialer_model_directory)

        portal = model.compute.nodes["portal"]
        portal["interfaces"]["eth0"]["network"] = "unknown-network"

        with self.assertRaisesRegex(
            ModelError,
            r"REF-002: Interface 'eth0' on node 'portal' "
            r"references unknown network 'unknown-network'",
        ):
            _validate_ref_002(model)

    def test_ref_003_rejects_unknown_application(self) -> None:
        model = Loader().load(self.out_dialer_model_directory)

        model.application.deployments["portal"]["applications"][0][
            "application"
        ] = "UnknownApplication"

        with self.assertRaisesRegex(
            ModelError,
            r"REF-003: Deployment 'portal' references unknown application "
            r"'UnknownApplication'",
        ):
            _validate_ref_003(model)

    def test_ref_004_rejects_unknown_external_interface_application(self) -> None:
        model = Loader().load(self.out_dialer_model_directory)

        model.platform.data["external_interfaces"]["metrics"]["targets"][0][
            "application"
        ] = "UnknownApplication"

        with self.assertRaisesRegex(
            ModelError,
            r"REF-004: External interface 'metrics' references unknown "
            r"application 'UnknownApplication'",
        ):
            _validate_ref_004(model)

    def test_ref_005_rejects_unknown_external_interface_endpoint(self) -> None:
        model = Loader().load(self.out_dialer_model_directory)

        model.platform.data["external_interfaces"]["metrics"]["targets"][0][
            "endpoint"
        ] = "unknown-endpoint"

        with self.assertRaisesRegex(
            ModelError,
            r"REF-005: External interface 'metrics' references unknown endpoint "
            r"'unknown-endpoint' on application 'Portal'",
        ):
            _validate_ref_005(model)

    def test_ref_005_ignores_unknown_application_owned_by_ref_004(self) -> None:
        model = Loader().load(self.out_dialer_model_directory)

        model.platform.data["external_interfaces"]["metrics"]["targets"][0][
            "application"
        ] = "UnknownApplication"

        _validate_ref_005(model)

    def test_ref_006_rejects_unknown_external_interface_source_network(
        self,
    ) -> None:
        model = Loader().load(self.out_dialer_model_directory)

        model.platform.data["external_interfaces"]["metrics"][
            "sourceNetwork"
        ] = "unknown-network"

        with self.assertRaisesRegex(
            ModelError,
            (
                r"REF-006: External interface 'metrics' references "
                r"unknown source network 'unknown-network'"
            ),
        ):
            _validate_ref_006(model)

    def test_ref_007_rejects_unknown_external_interface_target_network(
        self,
    ) -> None:
        model = Loader().load(self.out_dialer_model_directory)

        model.platform.data["external_interfaces"]["metrics"]["targets"][0][
            "network"
        ] = "unknown-network"

        with self.assertRaisesRegex(
            ModelError,
            (
                r"REF-007: External interface 'metrics' target "
                r"'Portal.metrics' references unknown network 'unknown-network'"
            ),
        ):
            _validate_ref_007(model)

    def test_ref_008_rejects_unknown_compute_node(self) -> None:
        model = Loader().load(self.out_dialer_model_directory)
        realization = load_realization(self.out_dialer_realization)

        realization.docker["hosts"]["workload"]["nodes"].append(
            "unknown-node"
        )

        with self.assertRaisesRegex(
            ModelError,
            (
                r"REF-008: Docker host 'workload' references "
                r"unknown compute node 'unknown-node'"
            ),
        ):
            _validate_ref_008(model, realization)

    def test_ref_009_rejects_duplicate_compute_node_placement(self) -> None:
        model = Loader().load(self.out_dialer_model_directory)
        realization = load_realization(self.out_dialer_realization)

        realization.docker["hosts"]["second-host"] = {
            "nodes": ["portal"],
        }

        with self.assertRaisesRegex(
            ModelError,
            (
                r"REF-009: Compute node 'portal' is assigned to multiple "
                r"Docker hosts: 'workload' and 'second-host'"
            ),
        ):
            _validate_ref_009(model, realization)

    def test_validates_realization_with_correct_references(self) -> None:
        model = Loader().load(self.out_dialer_model_directory)
        realization = load_realization(self.out_dialer_realization)

        validate_realization_references(model, realization)

if __name__ == "__main__":
    unittest.main()
