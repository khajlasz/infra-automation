"""Docker Compose generator for the Infrastructure Automation Framework."""

from typing import Any, Dict

from model.model import PlatformModel


class DockerComposeGenerator:
    """Generate a Docker Compose specification from a platform model."""

    def _generate_services(self, model: PlatformModel, compose_spec: Dict[str, Any]) -> None:
        """
        Generate service entries for compute nodes.
        
        Args:
            model: The loaded platform model
            compose_spec: The Docker Compose specification dictionary to update
        """
        for node_name in model.compute.nodes:
            # Add the node as a service with minimal configuration
            compose_spec["services"][node_name] = {}

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