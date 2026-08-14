from realization.resolver import resolve_network_ipam


def test_resolve_network_ipam():
    result = resolve_network_ipam(
        cidr="10.10.10.0/24",
        offset=128,
        prefix_length=28,
    )

    assert result == {
        "subnet": "10.10.10.0/24",
        "gateway": "10.10.10.1",
        "ip_range": "10.10.10.128/28",
    }

    