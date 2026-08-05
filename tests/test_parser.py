"""Tests for the YAML parser module."""

import os
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from model.parser import parse_yaml
from model.errors import ModelParseError

def test_parse_valid_yaml():
    """Test parsing valid YAML content."""
    # Create a temporary valid YAML file
    yaml_content = """
nodes:
  test_node:
    site: test_site
    computeProfile: medium
"""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        temp_file = f.name
    
    try:
        result = parse_yaml(Path(temp_file))
        assert "nodes" in result
        assert "test_node" in result["nodes"]
        assert result["nodes"]["test_node"]["site"] == "test_site"
    finally:
        os.unlink(temp_file)


def test_parse_invalid_yaml():
    """Test parsing invalid YAML content raises ModelParseError."""
    # Create a temporary invalid YAML file
    yaml_content = """
nodes:
  test_node:
    site: test_site
      invalid_indentation: value
"""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        temp_file = f.name
    
    try:
        parse_yaml(Path(temp_file))
        assert False, "Expected ModelParseError to be raised"
    except ModelParseError:
        pass  # Expected
    finally:
        os.unlink(temp_file)


def test_parse_empty_file():
    """Test parsing an empty YAML file."""
    yaml_content = ""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        temp_file = f.name
    
    try:
        result = parse_yaml(Path(temp_file))
        assert result is None
    finally:
        os.unlink(temp_file)