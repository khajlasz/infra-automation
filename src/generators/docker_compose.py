"""Docker Compose generator for the Infrastructure Automation Framework."""

from typing import Any, Dict

from model.model import PlatformModel
from generators.utils import to_kebab_case


class DockerComposeGenerator:
    """Generate a Docker Compose specification from a platform model."""

    def _build_image_name(self, deployment: Dict[str, Any]) -> str:
        """
        Build a Docker image name from a deployment dictionary.
        
        Args:
            deployment: The deployment dictionary
            
        Returns:
            A Docker image name in format <vendor>/<edition>:<version>
        """
        # Extract vendor, edition and version
        vendor = deployment["product"]["vendor"]
        edition = deployment["product"]["edition"]
        version = deployment["product"]["version"]
        
        # Process vendor: convert to lowercase
        vendor = vendor.lower()
        
        # Process edition: convert from PascalCase to kebab-case
        edition = to_kebab_case(edition)
        
        return f"{vendor}/{edition}:{version}"

    def _build_networks(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build Docker Compose networks dictionary from compute node interfaces.
        
        Args:
            node: The compute node dictionary
            
        Returns:
            A dictionary of networks for the Docker Compose service
        """
        networks = {}
        
        # Get all unique network names from interface definitions
        for interface in node["interfaces"].values():
            # Use the network name directly as specified in the platform model
            network_name = interface["network"]
            networks[network_name] = {}
        
        return networks

    def _generate_services(self, model: PlatformModel, compose_spec: Dict[str, Any]) -> None:
        """
        Generate service entries for compute nodes.
        
        Args:
            model: The loaded platform model
            compose_spec: The Docker Compose specification dictionary to update
        """
        services = compose_spec["services"]
        
        for node_name, node in model.compute.nodes.items():
            # Add the node as a service
            services[node_name] = {}
            service = services[node_name]
            
            # Generate the image from the deployment
            deployment_name = node["deployment"]
            deployment = model.application.deployments[deployment_name]
            service["image"] = self._build_image_name(deployment)
            
            # Set the hostname to the node name
            service["hostname"] = node_name
            
            # Add networks from interfaces
            service["networks"] = self._build_networks(node)

    def generate(self, model: PlatformModel) -> Dict[str, Any]:
        """
        Generate a Docker Compose specification from the platform model.
        
        Args:
            model: The loaded platform model
            
        Returns:
            A Python dictionary representing a partial Docker Compose spec 
            with services section containing entries for each compute node
        """
        # Initialize the Docker Compose structure
        compose_spec = {"services": {}}
        
        # Generate service entries from compute nodes
        self._generate_services(model, compose_spec)
        
        return compose_spec