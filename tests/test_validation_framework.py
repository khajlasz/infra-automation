"""Tests for semantic model validation."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from loader import Loader
from model import ModelError
from validation import validate_model
from validation.framework import (
    _validate_ref_001,
    _validate_ref_002,
    _validate_ref_003,
    _validate_ref_004,
    _validate_ref_005,
)


class SemanticValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).parents[1]
        self.minimal_model_directory = self.repo_root / "models" / "minimal"
        self.out_dialer_model_directory = self.repo_root / "models" / "out-dialer"

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

if __name__ == "__main__":
    unittest.main()
