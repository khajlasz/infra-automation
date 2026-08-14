from pathlib import Path

from realization import load_realization


def test_load_local_lab_realization():
    realization = load_realization(
        Path("realizations/out-dialer/local-lab.yaml")
    )

    assert realization.name == "local-lab"
    assert realization.docker["networkDriver"] == "macvlan"

    networks = realization.docker["networks"]

    assert networks["dmz"]["parent"] == "enp0s2"
    assert networks["internal"]["parent"] == "enp0s3"
    assert networks["database"]["parent"] == "enp0s4"

    assert networks["dmz"]["ipam"]["offset"] == 128
    assert networks["dmz"]["ipam"]["prefixLength"] == 28