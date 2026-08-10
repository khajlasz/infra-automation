"""Utility functions for Docker Compose generator."""

import re


def to_kebab_case(text: str) -> str:
    """
    Convert a PascalCase string to kebab-case.
    
    Args:
        text: The input string in PascalCase
        
    Returns:
        The string converted to kebab-case
    """
    # This regex finds sequences of letters followed by capital letters (except at the end)
    return re.sub(r'([a-z])([A-Z])', r'\1-\2', text).lower()