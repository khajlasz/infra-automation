from pathlib import Path

from realization import load_realization


def test_load_local_lab_realization():
    realization = load_realization(
        Path("realizations/out-dialer/local-lab.yaml")
    )

    assert realization.name == "local-lab"

    workload = realization.docker["hosts"]["workload"]

    assert workload["nodes"] == [
        "portal",
        "campaign",
        "call_simulator",
        "database",
    ]

    assert workload["networkDriver"] == "macvlan"

    assert "dmz" in workload["networks"]
    assert "internal" in workload["networks"]
    assert "database" in workload["networks"]

    assert "observability" not in realization.docker["hosts"]

    assert (
        realization.routeros["interfaces"]["observability"]["physicalInterface"]
        == "ether4"
    )