from pathlib import Path

from realization import load_realization


def test_load_local_lab_realization():
    realization = load_realization(
        Path("realizations/out-dialer/local-lab.yaml")
    )

    assert realization.name == "local-lab"
    
    assert "workload" in realization.docker["hosts"]
    assert "observability" in realization.docker["hosts"]
    
    workload_host = realization.docker["hosts"]["workload"]
    assert workload_host["networkDriver"] == "macvlan"

    networks = workload_host["networks"]

    assert networks["dmz"]["parent"] == "enp0s2"
    assert networks["internal"]["parent"] == "enp0s3"
    assert networks["database"]["parent"] == "enp0s4"

    assert networks["dmz"]["ipam"]["offset"] == 128
    assert networks["dmz"]["ipam"]["prefixLength"] == 28

    observability_host = realization.docker["hosts"]["observability"]

    assert observability_host["networkDriver"] == "macvlan"

    observability_network = observability_host["networks"]["observability"]

    assert observability_network["parent"] == "enp0s2"
    assert observability_network["ipam"]["offset"] == 128
    assert observability_network["ipam"]["prefixLength"] == 28
    
    assert realization.routeros["interfaces"]["dmz"]["physicalInterface"] == "ether1"
    assert realization.routeros["interfaces"]["internal"]["physicalInterface"] == "ether2"
    assert realization.routeros["interfaces"]["database"]["physicalInterface"] == "ether3"
