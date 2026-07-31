"""Tests for the platform model loader."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from loader import Loader
from model import ModelError


class LoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model_directory = Path(__file__).parents[1] / "models" / "minimal"

    def test_loads_telecom_model_by_domain(self) -> None:
        model = Loader().load(self.model_directory)

        self.assertIn("signalling", model.network.networks)
        self.assertIn("as01", model.compute.nodes)
        self.assertIn("bw-as", model.application.deployments)
        self.assertIn("small", model.compute.compute_profiles)

    def test_domain_keys_and_membership(self) -> None:
        model = Loader().load(self.model_directory)

        self.assertEqual(
            model.network.keys(),
            ["device_profiles", "devices", "networks", "policies", "sites"],
        )
        self.assertIn("networks", model.network)
        self.assertNotIn("missing", model.network)

    def test_missing_model_object_raises_attribute_error(self) -> None:
        model = Loader().load(self.model_directory)

        with self.assertRaises(AttributeError):
            model.network.missing

    def test_domain_representation_lists_loaded_objects(self) -> None:
        model = Loader().load(self.model_directory)

        self.assertEqual(
            repr(model.network),
            "ModelDomain(objects=['device_profiles', 'devices', 'networks', "
            "'policies', 'sites'])",
        )

    def test_preserves_nested_directory_hierarchy(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            model_directory = Path(temporary_directory)
            nested_file = model_directory / "network" / "nested" / "example.yaml"
            nested_file.parent.mkdir(parents=True)
            nested_file.write_text(
                "example:\n  value: example\n", encoding="utf-8"
            )

            model = Loader().load(model_directory)

        self.assertEqual(model.network.data["nested"]["example"], {"value": "example"})

    def test_incorrect_root_key_raises_model_error(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            model_directory = Path(temporary_directory)
            network_directory = model_directory / "network"
            network_directory.mkdir()
            (network_directory / "custom.yaml").write_text(
                "other: value\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(
                ModelError, "Expected root key 'custom'.*found 'other'"
            ):
                Loader().load(model_directory)

    def test_multiple_root_keys_raise_model_error(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            model_directory = Path(temporary_directory)
            network_directory = model_directory / "network"
            network_directory.mkdir()
            (network_directory / "multiple.yaml").write_text(
                "multiple: value\nother: value\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(ModelError, "exactly one root key"):
                Loader().load(model_directory)

    def test_empty_root_mapping_raises_model_error(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            model_directory = Path(temporary_directory)
            network_directory = model_directory / "network"
            network_directory.mkdir()
            (network_directory / "empty.yaml").write_text("", encoding="utf-8")

            with self.assertRaisesRegex(ModelError, "exactly one root key"):
                Loader().load(model_directory)
