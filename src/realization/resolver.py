from ipaddress import ip_network


def resolve_network_ipam(
    cidr: str,
    offset: int,
    prefix_length: int,
) -> dict[str, str]:
    """Resolve Docker IPAM values from a logical network and realization policy."""

    network = ip_network(cidr)

    gateway = network.network_address + 1
    range_address = network.network_address + offset
    ip_range = ip_network(
        f"{range_address}/{prefix_length}",
        strict=True,
    )

    return {
        "subnet": str(network),
        "gateway": str(gateway),
        "ip_range": str(ip_range),
    }