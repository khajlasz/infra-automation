from pathlib import Path

from generators.terraform_routeros import TerraformRouterOSGenerator
from loader.loader import Loader
from realization import load_realization


def test_generate_routeros_interfaces_and_gateways():
    model = Loader().load(Path("models/out-dialer"))
    realization = load_realization(
        Path("realizations/out-dialer/local-lab.yaml")
    )

    generator = TerraformRouterOSGenerator()
    result = generator.generate(model, realization)

    interfaces = result["resource"]["routeros_interface_ethernet"]

    assert interfaces["dmz"] == {
        "name": "dmz",
        "factory_name": "ether1",
    }

    assert interfaces["internal"] == {
        "name": "internal",
        "factory_name": "ether2",
    }

    assert interfaces["database"] == {
        "name": "database",
        "factory_name": "ether3",
    }

    addresses = result["resource"]["routeros_ip_address"]

    assert addresses["dmz_gateway"] == {
        "address": "10.10.10.1/24",
        "interface": "dmz",
        "comment": "DMZ gateway",
    }

    assert addresses["internal_gateway"] == {
        "address": "10.10.20.1/24",
        "interface": "internal",
        "comment": "Internal gateway",
    }

    assert addresses["database_gateway"] == {
        "address": "10.10.30.1/24",
        "interface": "database",
        "comment": "Database gateway",
    }

    address_lists = result["resource"]["routeros_ip_firewall_addr_list"]

    assert address_lists["dmz"] == {
        "list": "lab-networks",
        "address": "10.10.10.0/24",
        "comment": "DMZ",
    }

    assert address_lists["internal"] == {
        "list": "lab-networks",
        "address": "10.10.20.0/24",
        "comment": "Internal",
    }

    assert address_lists["database"] == {
        "list": "lab-networks",
        "address": "10.10.30.0/24",
        "comment": "Database",
    }

    filters = result["resource"]["routeros_ip_firewall_filter"]

    assert list(filters) == [
        "allow_established_related",
        "drop_invalid",
        "allow_dmz_to_internal",
        "allow_internal_to_database",
        "deny_other_interzone",
    ]

    assert filters["allow_established_related"] == {
        "chain": "forward",
        "action": "accept",
        "connection_state": "established,related,untracked",
        "comment": "LAB: allow established and related",
    }

    assert filters["drop_invalid"] == {
        "chain": "forward",
        "action": "drop",
        "connection_state": "invalid",
        "comment": "LAB: drop invalid",
    }

    assert filters["allow_dmz_to_internal"] == {
        "chain": "forward",
        "action": "accept",
        "src_address": "10.10.10.0/24",
        "dst_address": "10.10.20.0/24",
        "comment": "Allow DMZ traffic to Internal network",
    }

    assert filters["allow_internal_to_database"] == {
        "chain": "forward",
        "action": "accept",
        "src_address": "10.10.20.0/24",
        "dst_address": "10.10.30.0/24",
        "comment": "Allow Internal traffic to Database network",
    }

    assert filters["deny_other_interzone"] == {
        "chain": "forward",
        "action": "drop",
        "src_address_list": "lab-networks",
        "dst_address_list": "lab-networks",
        "log": True,
        "log_prefix": "LAB-DENY ",
        "comment": "LAB: deny other inter-zone traffic",
    }

def test_serialize_returns_terraform_hcl():
    model = Loader().load(Path("models/out-dialer"))
    realization = load_realization(
        Path("realizations/out-dialer/local-lab.yaml")
    )

    generator = TerraformRouterOSGenerator()
    spec = generator.generate(model, realization)
    result = generator.serialize(spec)

    assert 'resource "routeros_interface_ethernet" "dmz" {' in result
    assert 'factory_name = "ether1"' in result

    assert 'resource "routeros_ip_address" "dmz_gateway" {' in result
    assert 'address = "10.10.10.1/24"' in result

    assert (
        'resource "routeros_ip_firewall_filter" "allow_dmz_to_internal" {'
        in result
    )
    assert 'src_address = "10.10.10.0/24"' in result
    assert 'dst_address = "10.10.20.0/24"' in result

    assert 'resource "routeros_ip_firewall_filter" "deny_other_interzone" {' in result
    assert "log = true" in result