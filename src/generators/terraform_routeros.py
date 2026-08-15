from typing import Any

from model.model import PlatformModel
from realization.model import Realization
from realization.resolver import resolve_network


class TerraformRouterOSGenerator:
    """Generate RouterOS Terraform configuration."""

    def _generate_interfaces(
        self,
        model: PlatformModel,
        realization: Realization,
        resources: dict[str, Any],
    ) -> None:
        interfaces = realization.routeros["interfaces"]

        resources["routeros_interface_ethernet"] = {}

        for network_name in model.network.networks:
            interface = interfaces[network_name]

            resources["routeros_interface_ethernet"][network_name] = {
                "name": network_name,
                "factory_name": interface["physicalInterface"],
            }

    @staticmethod
    def _display_name(name: str) -> str:
        return name.upper() if name == "dmz" else name.capitalize()

    def _generate_gateway_addresses(
        self,
        model: PlatformModel,
        resources: dict[str, Any],
    ) -> None:
        resources["routeros_ip_address"] = {}

        for network_name, network in model.network.networks.items():
            resolved = resolve_network(network["subnet"]["cidr"])

            resources["routeros_ip_address"][f"{network_name}_gateway"] = {
                "address": resolved["gateway_cidr"],
                "interface": network_name,
                "comment": f"{self._display_name(network_name)} gateway",
            }

    def _generate_firewall_address_lists(
        self,
        model: PlatformModel,
        resources: dict[str, Any],
    ) -> None:
        resources["routeros_ip_firewall_addr_list"] = {}

        for network_name, network in model.network.networks.items():
            resolved = resolve_network(network["subnet"]["cidr"])

            resources["routeros_ip_firewall_addr_list"][network_name] = {
                "list": "lab-networks",
                "address": resolved["subnet"],
                "comment": self._display_name(network_name),
            }

    def _generate_firewall_filters(
        self,
        model: PlatformModel,
        resources: dict[str, Any],
    ) -> None:
        filters: dict[str, Any] = {}

        # RouterOS backend baseline: allow return traffic for established flows.
        filters["allow_established_related"] = {
            "chain": "forward",
            "action": "accept",
            "connection_state": "established,related,untracked",
            "comment": "LAB: allow established and related",
        }

        # RouterOS backend baseline: drop invalid connection state.
        filters["drop_invalid"] = {
            "chain": "forward",
            "action": "drop",
            "connection_state": "invalid",
            "comment": "LAB: drop invalid",
        }

        # Platform Model policies.
        for policy_name, policy in model.network.policies.items():
            source_network = model.network.networks[policy["from"]]
            destination_network = model.network.networks[policy["to"]]

            source = resolve_network(source_network["subnet"]["cidr"])
            destination = resolve_network(destination_network["subnet"]["cidr"])

            action = {
                "allow": "accept",
                "deny": "drop",
            }[policy["action"]]

            terraform_name = policy_name.replace("-", "_")

            filters[terraform_name] = {
                "chain": "forward",
                "action": action,
                "src_address": source["subnet"],
                "dst_address": destination["subnet"],
                "comment": policy["description"],
            }

        # RouterOS backend enforcement: deny any remaining inter-zone traffic.
        filters["deny_other_interzone"] = {
            "chain": "forward",
            "action": "drop",
            "src_address_list": "lab-networks",
            "dst_address_list": "lab-networks",
            "log": True,
            "log_prefix": "LAB-DENY ",
            "comment": "LAB: deny other inter-zone traffic",
        }

        resources["routeros_ip_firewall_filter"] = filters

    def generate(
        self,
        model: PlatformModel,
        realization: Realization,
    ) -> dict[str, Any]:
        resources: dict[str, Any] = {}

        self._generate_interfaces(model, realization, resources)
        self._generate_gateway_addresses(model, resources)
        self._generate_firewall_address_lists(model, resources)
        self._generate_firewall_filters(model, resources)

        return {
            "resource": resources,
        }

    def serialize(self, spec: dict[str, Any]) -> str:
        """Serialize generated RouterOS resources to Terraform HCL."""

        lines: list[str] = []

        for resource_type, resources in spec["resource"].items():
            for resource_name, attributes in resources.items():
                lines.append(
                    f'resource "{resource_type}" "{resource_name}" {{'
                )

                for key, value in attributes.items():
                    if isinstance(value, bool):
                        rendered_value = "true" if value else "false"
                    elif isinstance(value, str):
                        escaped_value = value.replace("\\", "\\\\").replace('"', '\\"')
                        rendered_value = f'"{escaped_value}"'
                    else:
                        raise TypeError(
                            f"Unsupported Terraform value type: {type(value).__name__}"
                        )

                    lines.append(f"  {key} = {rendered_value}")

                lines.append("}")
                lines.append("")

        return "\n".join(lines)