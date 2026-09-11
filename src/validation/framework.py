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
    
    # Run all validation rules
    logger.info("Starting semantic validation")
    
    # Simple rule registry - execute rules in order
    RULES = [
        _validate_ref_001,
        _validate_ref_002,
        _validate_ref_003,
        _validate_ref_004,
        _validate_ref_005,
    ]
    
    for rule in RULES:
        rule(model)
    
    logger.info("Semantic validation completed successfully")


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

def _validate_ref_002(model) -> None:
    """Validate REF-002: Interface references an existing network.

    Every interface SHALL reference an existing network.

    Args:
        model: The loaded platform model

    Raises:
        ModelError: If any interface references a non-existing network
    """
    logger.info("Running REF-002 validation")

    available_networks = set(model.network.networks.keys())

    for node_name, node in model.compute.nodes.items():
        for interface_name, interface in node.get("interfaces", {}).items():
            network_ref = interface.get("network")

            if network_ref not in available_networks:
                logger.error(
                    "REF-002: Interface '%s' on node '%s' references unknown network '%s'",
                    interface_name,
                    node_name,
                    network_ref,
                )
                raise ModelError(
                    f"REF-002: Interface '{interface_name}' on node "
                    f"'{node_name}' references unknown network '{network_ref}'"
                )


def _validate_ref_003(model) -> None:
    """Validate REF-003: Deployment references an existing application.

    Every deployment SHALL reference an existing application.

    Args:
        model: The loaded platform model

    Raises:
        ModelError: If any deployment references a non-existing application
    """
    logger.info("Running REF-003 validation")

    available_applications = set(model.application.applications.keys())

    for deployment_name, deployment in model.application.deployments.items():
        for application_ref in deployment.get("applications", []):
            application_name = application_ref.get("application")

            if application_name not in available_applications:
                logger.error(
                    "REF-003: Deployment '%s' references unknown application '%s'",
                    deployment_name,
                    application_name,
                )
                raise ModelError(
                    f"REF-003: Deployment '{deployment_name}' references "
                    f"unknown application '{application_name}'"
                )


def _validate_ref_004(model) -> None:
    """Validate REF-004: External interface target references an existing application.

    Every external interface target SHALL reference an existing application.

    Args:
        model: The loaded platform model

    Raises:
        ModelError: If any external interface target references a non-existing application
    """
    logger.info("Running REF-004 validation")

    available_applications = set(model.application.applications.keys())

    external_interfaces = model.platform.data.get("external_interfaces", {})

    for interface_name, external_interface in external_interfaces.items():
        for target in external_interface.get("targets", []):
            application_name = target.get("application")

            if application_name not in available_applications:
                logger.error(
                    "REF-004: External interface '%s' references unknown application '%s'",
                    interface_name,
                    application_name,
                )
                raise ModelError(
                    f"REF-004: External interface '{interface_name}' references "
                    f"unknown application '{application_name}'"
                )


def _validate_ref_005(model) -> None:
    """Validate REF-005: External interface target references an existing application endpoint.

    Every external interface target SHALL reference an endpoint defined by its
    referenced application.

    Args:
        model: The loaded platform model

    Raises:
        ModelError: If any external interface target references a non-existing endpoint
    """
    logger.info("Running REF-005 validation")

    applications = model.application.applications
    external_interfaces = model.platform.data.get("external_interfaces", {})

    for interface_name, external_interface in external_interfaces.items():
        for target in external_interface.get("targets", []):
            application_name = target.get("application")
            endpoint_name = target.get("endpoint")

            application = applications.get(application_name)

            if application is None:
                # REF-004 owns this failure.
                continue

            available_endpoints = application.get("endpoints", {})

            if endpoint_name not in available_endpoints:
                logger.error(
                    "REF-005: External interface '%s' references unknown endpoint '%s' "
                    "on application '%s'",
                    interface_name,
                    endpoint_name,
                    application_name,
                )
                raise ModelError(
                    f"REF-005: External interface '{interface_name}' references "
                    f"unknown endpoint '{endpoint_name}' on application "
                    f"'{application_name}'"
                )
