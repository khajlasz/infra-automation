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

    def test_serialize_returns_valid_yaml(self) -> None:
        """Test that serialize() returns valid YAML starting with services:."""
        model = self.loader.load(self.model_directory)
        compose_spec = self.generator.generate(model)
        yaml_output = self.generator.serialize(compose_spec)
        
        # Should start with "services:"
        self.assertTrue(yaml_output.startswith("services:"), "YAML should start with 'services:'")

    def test_serialize_includes_services_section(self) -> None:
        """Test that serialized output includes services section."""
        model = self.loader.load(self.model_directory)
        compose_spec = self.generator.generate(model)
        yaml_output = self.generator.serialize(compose_spec)
        
        # Should contain "services:" 
        self.assertIn("services:", yaml_output)

    def test_serialize_includes_expected_service_names(self) -> None:
        """Test that serialized output contains expected service names."""
        model_directory = Path(__file__).parents[1] / "models" / "out-dialer"
        model = self.loader.load(model_directory)
        compose_spec = self.generator.generate(model)
        yaml_output = self.generator.serialize(compose_spec)
        
        # Should contain all expected node names from the model
        expected_services = {"portal", "campaign", "call_simulator", "database"}
        for service in expected_services:
            self.assertIn(f"{service}:", yaml_output)

    def test_serialize_includes_image_hostname_networks_and_ports(self) -> None:
        """Test that serialized output contains image, hostname, networks and ports."""
        model_directory = Path(__file__).parents[1] / "models" / "out-dialer"
        model = self.loader.load(model_directory)
        compose_spec = self.generator.generate(model)
        yaml_output = self.generator.serialize(compose_spec)
        
        # Check that the output contains various expected elements
        self.assertIn("image:", yaml_output)
        self.assertIn("hostname:", yaml_output)
        self.assertIn("networks:", yaml_output)
        self.assertIn("ports:", yaml_output)

    def test_generate_networks_section_exists(self) -> None:
        """Test that the top-level networks section is generated."""
        model_directory = Path(__file__).parents[1] / "models" / "out-dialer"
        model = self.loader.load(model_directory)
        result = self.generator.generate(model)
        
        # Should have a networks section at the top level
        self.assertIn("networks", result)
        self.assertIsInstance(result["networks"], dict)

    def test_generate_networks_from_model(self) -> None:
        """Test that all platform model networks appear in the Docker Compose networks."""
        model_directory = Path(__file__).parents[1] / "models" / "out-dialer"
        model = self.loader.load(model_directory)
        result = self.generator.generate(model)
        
        # Get expected network names from the model
        expected_networks = set(model.network.networks.keys())
        
        # Get actual network names from generated spec
        actual_networks = set(result["networks"].keys())
        
        # Should have exactly the same networks
        self.assertEqual(actual_networks, expected_networks)
        self.assertEqual(len(actual_networks), len(expected_networks))
        
        # Each network should be empty (no extra attributes)
        for network_name in actual_networks:
            self.assertIn(network_name, result["networks"])
            self.assertIsInstance(result["networks"][network_name], dict)
            self.assertEqual(len(result["networks"][network_name]), 0)


if __name__ == "__main__":
    unittest.main()