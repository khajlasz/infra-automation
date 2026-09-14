"""Tests for the Docker Compose CLI command."""

import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import os

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from cli import main


class CLIDockerComposeCommandTests(unittest.TestCase):
    def test_generate_docker_compose_command_creates_host_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(__file__).parents[1]

            model_dir = repo_root / "models" / "out-dialer"
            realization_path = (
                repo_root
                / "realizations"
                / "out-dialer"
                / "local-lab.yaml"
            )

            output = Path(tmp_dir) / "docker-compose.yaml"

            with patch(
                "sys.argv",
                [
                    "cli.py",
                    "generate",
                    "docker-compose",
                    str(model_dir),
                    "--realization",
                    str(realization_path),
                    "--output",
                    str(output),
                ],
            ):
                result = main()

            self.assertEqual(result, 0)

            workload_output = output.with_name(
                f"{output.stem}.workload{output.suffix}"
            )

            self.assertTrue(workload_output.exists())

            content = workload_output.read_text()

            self.assertIn("services:", content)
            self.assertIn("portal:", content)
            self.assertIn("campaign:", content)
            self.assertIn("call_simulator:", content)
            self.assertIn("database:", content)

    def test_generate_docker_compose_command_uses_default_output_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(__file__).parents[1]

            model_dir = repo_root / "models" / "out-dialer"
            realization_path = (
                repo_root
                / "realizations"
                / "out-dialer"
                / "local-lab.yaml"
            )

            original_cwd = os.getcwd()

            try:
                os.chdir(tmp_dir)

                with patch(
                    "sys.argv",
                    [
                        "cli.py",
                        "generate",
                        "docker-compose",
                        str(model_dir),
                        "--realization",
                        str(realization_path),
                    ],
                ):
                    result = main()

                self.assertEqual(result, 0)

                output_file = (
                    Path(tmp_dir)
                    / "docker-compose.workload.yaml"
                )

                self.assertTrue(output_file.exists())

            finally:
                os.chdir(original_cwd)

    def test_generate_docker_compose_requires_realization(self) -> None:
        repo_root = Path(__file__).parents[1]
        model_dir = repo_root / "models" / "out-dialer"

        with patch(
            "sys.argv",
            [
                "cli.py",
                "generate",
                "docker-compose",
                str(model_dir),
            ],
        ):
            with self.assertRaises(SystemExit):
                main()

    def test_generate_docker_compose_command_uses_default_output_name(self) -> None:
        """Use docker-compose.yaml as the default base output name."""

        repo_root = Path(__file__).parents[1]
        model_dir = repo_root / "models" / "out-dialer"
        realization_path = (
            repo_root
            / "realizations"
            / "out-dialer"
            / "local-lab.yaml"
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            original_cwd = Path.cwd()

            try:
                os.chdir(tmp_dir)

                with patch(
                    "sys.argv",
                    [
                        "cli.py",
                        "generate",
                        "docker-compose",
                        str(model_dir),
                        "--realization",
                        str(realization_path),
                    ],
                ):
                    result = main()

                self.assertEqual(result, 0)

                output_file = (
                    Path(tmp_dir)
                    / "docker-compose.workload.yaml"
                )

                self.assertTrue(output_file.exists())
                self.assertFalse(
                    (Path(tmp_dir) / "docker-compose.yaml").exists()
                )

            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()