"""Framework for semantic model validation."""

from pathlib import Path

from model import ModelError
from observability import get_logger
from loader import Loader

logger = get_logger(__name__)


def validate_model(model_directory: Path) -> None:
    """Validate a model against implemented rules.
    
    Args:
        model_directory: Path to the directory containing the model files
        
    Raises:
        ModelError: If any validation rule fails
    """
    logger.info("Validating model %s", model_directory)
    
    # Load the complete model first
    model = Loader().load(model_directory)
    
    # Run all validation rules, currently only REF-001 implemented
    _validate_ref_001(model)


def _validate_ref_001(model) -> None:
    """Validate REF-001: Node references an existing site.
    
    Every node SHALL reference an existing site.
    
    Args:
        model: The loaded platform model
        
    Raises:
        ModelError: If any node references a non-existing site
    """
    logger.info("Running REF-001 validation")
    
    available_sites = set(model.network.sites.keys())
    
    for node_name, node in model.compute.nodes.items():
        site_ref = node.get('site')
        
        if site_ref not in available_sites:
            logger.error("REF-001: Node '%s' references unknown site '%s'", 
                        node_name, site_ref)
            raise ModelError(f"REF-001: Node '{node_name}' references unknown site '{site_ref}'")