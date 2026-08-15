"""Tests for the RouterOS Terraform CLI command."""

from pathlib import Path
import tempfile
from unittest.mock import patch

from cli import main


def test_generate_terraform_routeros_command_creates_file() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        model_dir = Path(__file__).parents[1] / "models" / "out-dialer"
        realization = (
            Path(__file__).parents[1]
            / "realizations"
            / "out-dialer"
            / "local-lab.yaml"
        )
        output_file = Path(tmp_dir) / "generated.tf"

        with patch(
            "sys.argv",
            [
                "cli.py",
                "generate",
                "terraform-routeros",
                str(model_dir),
                "--realization",
                str(realization),
                "--output",
                str(output_file),
            ],
        ):
            result = main()

        assert result == 0
        assert output_file.exists()

        content = output_file.read_text(encoding="utf-8")

        assert 'resource "routeros_interface_ethernet" "dmz"' in content
        assert 'factory_name = "ether1"' in content
        assert 'resource "routeros_ip_address" "dmz_gateway"' in content
        assert (
            'resource "routeros_ip_firewall_filter" '
            '"allow_dmz_to_internal"'
        ) in content