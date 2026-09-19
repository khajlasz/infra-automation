"""Docker Compose generator for the Infrastructure Automation Framework."""

from typing import Any, Dict

import yaml

from model.model import PlatformModel
from realization.model import Realization
from realization.resolver import resolve_network_ipam
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

    def _build_ports(
        self,
        deployment: Dict[str, Any],
        model: PlatformModel,
    ) -> list[str]:
        """
        Build Docker Compose ports list from application endpoints.
        
        Args:
            deployment: The deployment dictionary
            model: The loaded platform model
            
        Returns:
            A list of port mappings in the format ["<port>:<port>", ...]
        """
        ports = set()

        for app_ref in deployment["applications"]:
            app_definition = model.application.applications[
                app_ref["application"]
            ]
            
            # Handle cases where endpoints might not be defined (e.g. in minimal model)
            if "endpoints" in app_definition:
                for endpoint in app_definition["endpoints"].values():
                    ports.add(f'{endpoint["port"]}:{endpoint["port"]}')

        return sorted(ports)

    def _get_required_networks(
        self,
        model: PlatformModel,
        node_names: list[str],
    ) -> set[str]:
        """Return logical networks required by the selected compute nodes."""
        required_networks = set()

        for node_name in node_names:
            node = model.compute.nodes[node_name]

            for interface in node["interfaces"].values():
                required_networks.add(interface["network"])

        return required_networks

    def _generate_networks(
        self,
        model: PlatformModel,
        compose_spec: Dict[str, Any],
        host: Dict[str, Any],
        network_names: set[str],
    ) -> None:
        """Generate top-level Docker Compose networks."""

        compose_spec["networks"] = {}
        networks = compose_spec["networks"]

        driver = host["networkDriver"]
        realized_networks = host["networks"]

        for network_name in sorted(network_names):
            network = model.network.networks[network_name]
            realization_network = realized_networks[network_name]

            cidr = network["subnet"]["cidr"]
            ipam_config = realization_network["ipam"]

            resolved_ipam = resolve_network_ipam(
                cidr=cidr,
                offset=ipam_config["offset"],
                prefix_length=ipam_config["prefixLength"],
            )

            networks[network_name] = {
                "name": f"{network_name}-net",
                "driver": driver,
                "driver_opts": {
                    "parent": realization_network["parent"],
                },
                "ipam": {
                    "config": [
                        resolved_ipam,
                    ],
                },
            }

    def _generate_services(
        self,
        model: PlatformModel,
        compose_spec: Dict[str, Any],
        node_names: list[str],
    ) -> None:
        """Generate service entries for selected compute nodes."""

        services = compose_spec["services"]

        for node_name in node_names:
            node = model.compute.nodes[node_name]

            service = {}
            services[node_name] = service

            deployment_name = node["deployment"]
            deployment = model.application.deployments[deployment_name]

            service["image"] = self._build_image_name(deployment)
            service["hostname"] = node_name
            service["networks"] = self._build_networks(node)

            ports = self._build_ports(deployment, model)
            if ports:
                service["ports"] = ports

    def generate(
        self,
        model: PlatformModel,
        realization: Realization | None = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Generate one Docker Compose specification per Docker host."""

        if realization is None:
            raise ValueError(
                "Docker Compose generation requires a realization"
            )

        compose_specs = {}

        for host_name, host in realization.docker.get("hosts", {}).items():
            node_names = host.get("nodes", [])

            if not node_names:
                continue

            compose_spec = {"services": {}}

            required_networks = self._get_required_networks(
                model,
                node_names,
            )

            self._generate_services(
                model,
                compose_spec,
                node_names,
            )

            self._generate_networks(
                model,
                compose_spec,
                host,
                required_networks,
            )

            compose_specs[host_name] = compose_spec

        return compose_specs

    def serialize(self, compose_spec: Dict[str, Any]) -> str:
        """
        Serialize a Docker Compose specification to YAML.
        
        Args:
            compose_spec: The Docker Compose specification dictionary
            
        Returns:
            A YAML string representing the Docker Compose specification
        """
        return yaml.safe_dump(
            compose_spec,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            indent=2,
            width=80
        )