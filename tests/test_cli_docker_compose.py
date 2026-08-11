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
    def test_generate_docker_compose_command_creates_file(self) -> None:
        """Test that generate docker-compose command creates a docker-compose.yaml file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Use the minimal model for testing
            model_dir = Path(__file__).parents[1] / "models" / "minimal"
            
            # Change to temp directory to write output file
            with patch('sys.argv', [
                'cli.py', 
                'generate', 
                'docker-compose',
                str(model_dir),
                '--output', 
                f'{tmp_dir}/docker-compose.yaml'
            ]):
                # This should not raise an exception
                result = main()
                
                # Check that file was created
                output_file = Path(tmp_dir) / "docker-compose.yaml"
                self.assertTrue(output_file.exists(), "docker-compose.yaml should be created")
                
                # Check that it contains expected content
                content = output_file.read_text()
                self.assertIn("services:", content)
                self.assertIn("node1:", content)

    def test_generate_docker_compose_command_defaults_to_docker_compose_yaml(self) -> None:
        """Test that generate docker-compose command defaults to docker-compose.yaml."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Use the minimal model for testing
            model_dir = Path(__file__).parents[1] / "models" / "minimal"
            
            # Change working directory to temp dir to test default output location
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)
                
                with patch('sys.argv', [
                    'cli.py', 
                    'generate', 
                    'docker-compose',
                    str(model_dir)
                ]):
                    result = main()
                    
                    # Check that file was created in current directory
                    output_file = Path(tmp_dir) / "docker-compose.yaml"
                    self.assertTrue(output_file.exists(), "docker-compose.yaml should be created in working directory")
                    
                    content = output_file.read_text()
                    self.assertIn("services:", content)
                    self.assertIn("node1:", content)
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()