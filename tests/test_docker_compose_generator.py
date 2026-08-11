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

    def test_generate_networks(self) -> None:
        """Test that Docker Compose networks are generated from compute node interfaces."""
        model_directory = Path(__file__).parents[1] / "models" / "out-dialer"
        model = self.loader.load(model_directory)
        result = self.generator.generate(model)
        
        # Test each service for expected networks
        expected_networks = {
            "portal": {"dmz", "internal"},
            "campaign": {"internal", "database"},
            "call_simulator": {"internal"},
            "database": {"database"}
        }
        
        for node_name, expected_node_networks in expected_networks.items():
            with self.subTest(node=node_name):
                self.assertIn("networks", result["services"][node_name])
                actual_networks = set(result["services"][node_name]["networks"].keys())
                self.assertEqual(actual_networks, expected_node_networks)

    def test_generate_ports(self) -> None:
        """Test that Docker Compose ports are generated from application endpoints."""
        model_directory = Path(__file__).parents[1] / "models" / "out-dialer"
        model = self.loader.load(model_directory)
        result = self.generator.generate(model)
        
        # Define expected ports based on the model
        expected_ports = {
            "portal": ["8443:8443", "8444:8444", "9090:9090"],  # Portal + Authentication apps
            "campaign": ["8080:8080", "9090:9090"],  # CampaignManager has rest and metrics endpoints  
            "call_simulator": ["8081:8081", "9090:9090"],  # CallSimulator has rest and metrics endpoints
            "database": ["5432:5432"]  # PostgreSQL has sql endpoint
        }
        
        for node_name, expected_node_ports in expected_ports.items():
            with self.subTest(node=node_name):
                if expected_node_ports:  # Only check services that have ports
                    self.assertIn("ports", result["services"][node_name])
                    actual_ports = result["services"][node_name]["ports"]
                    self.assertEqual(sorted(actual_ports), sorted(expected_node_ports))
                else:  # Services without ports should not have ports key
                    self.assertNotIn("ports", result["services"][node_name])


if __name__ == "__main__":
    unittest.main()