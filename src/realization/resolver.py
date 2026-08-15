from ipaddress import ip_network


def resolve_network(cidr: str) -> dict[str, str]:
    """Resolve generic network values derived from a CIDR."""

    network = ip_network(cidr)
    gateway = network.network_address + 1

    return {
        "subnet": str(network),
        "gateway": str(gateway),
        "gateway_cidr": f"{gateway}/{network.prefixlen}",
    }


def resolve_network_ipam(
    cidr: str,
    offset: int,
    prefix_length: int,
) -> dict[str, str]:
    """Resolve Docker-specific IPAM values."""

    resolved_network = resolve_network(cidr)
    network = ip_network(cidr)

    range_address = network.network_address + offset
    ip_range = ip_network(
        f"{range_address}/{prefix_length}",
        strict=True,
    )

    return {
        "subnet": resolved_network["subnet"],
        "gateway": resolved_network["gateway"],
        "ip_range": str(ip_range),
    }