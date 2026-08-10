"""Tests for the Docker Compose generator."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from generators.docker_compose import DockerComposeGenerator
from loader import Loader


class DockerComposeGeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model_directory = Path(__file__).parents[1] / "models" / "minimal"
        self.loader = Loader()
        self.generator = DockerComposeGenerator()

    def test_generate_creates_services_section(self) -> None:
        model = self.loader.load(self.model_directory)
        result = self.generator.generate(model)
        
        self.assertIn("services", result)
        self.assertIsInstance(result["services"], dict)

    def test_generate_includes_all_nodes_as_services(self) -> None:
        model = self.loader.load(self.model_directory)
        result = self.generator.generate(model)
        
        # Should create a service entry for each node
        self.assertIn("node1", result["services"])
        self.assertEqual(len(result["services"]), 1)

    def test_generate_with_out_dialer_model(self) -> None:
        """Test generator with out-dialer model that has multiple nodes."""
        model_directory = Path(__file__).parents[1] / "models" / "out-dialer"
        model = self.loader.load(model_directory)
        result = self.generator.generate(model)
        
        # Should create services for each node in the model
        expected_nodes = set(model.compute.nodes.keys())
        actual_services = set(result["services"].keys())
        
        self.assertEqual(actual_services, expected_nodes)
        self.assertEqual(len(result["services"]), len(expected_nodes))

    def test_generate_images(self) -> None:
        """Test that Docker images are generated correctly from model data."""
        model_directory = Path(__file__).parents[1] / "models" / "out-dialer"
        model = self.loader.load(model_directory)
        result = self.generator.generate(model)
        
        # Verify image names are correctly derived from the model
        for node_name, node in model.compute.nodes.items():
            with self.subTest(node=node_name):
                if "deployment" in node:
                    deployment_name = node["deployment"]
                    deployment = model.application.deployments[deployment_name]
                    
                    # Build expected image name using same logic as generator
                    vendor = deployment["product"]["vendor"].lower()
                    edition = deployment["product"]["edition"]
                    # Convert PascalCase to kebab-case
                    import re
                    edition = re.sub(r'([a-z])([A-Z])', r'\1-\2', edition).lower()
                    version = deployment["product"]["version"]
                    expected_image = f"{vendor}/{edition}:{version}"
                    
                    self.assertIn("image", result["services"][node_name])
                    self.assertEqual(result["services"][node_name]["image"], expected_image)

    def test_generate_hostnames(self) -> None:
        """Test that Docker hostnames are generated correctly from compute node names."""
        model_directory = Path(__file__).parents[1] / "models" / "out-dialer"
        model = self.loader.load(model_directory)
        result = self.generator.generate(model)
        
        # Verify that each service has a hostname equal to its node name
        for node_name, node in model.compute.nodes.items():
            with self.subTest(node=node_name):
                self.assertIn("hostname", result["services"][node_name])
                self.assertEqual(result["services"][node_name]["hostname"], node_name)


if __name__ == "__main__":
    unittest.main()