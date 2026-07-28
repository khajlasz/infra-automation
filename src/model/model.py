"""Internal dictionary-based platform model."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelDomain:
    """A model domain whose YAML files are exposed as attributes.

    Every YAML file loaded into a domain becomes an attribute named after the
    file. For example, ``network/networks.yaml`` becomes
    ``model.network.networks`` and ``compute/nodes.yaml`` becomes
    ``model.compute.nodes``.
    """

    data: dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, name: str) -> Any:
        try:
            return self.data[name]
        except KeyError as error:
            raise AttributeError(name) from error

    def keys(self) -> list[str]:
        """Return the names of model objects available in this domain."""
        return list(self.data)

    def __contains__(self, name: str) -> bool:
        """Return whether a model object exists in this domain."""
        return name in self.data

    def __repr__(self) -> str:
        """Return a concise representation for interactive use."""
        return f"ModelDomain(objects={self.keys()!r})"


@dataclass(repr=False)
class PlatformDomain(ModelDomain):
    """Platform model data."""


@dataclass(repr=False)
class NetworkDomain(ModelDomain):
    """Network model data."""


@dataclass(repr=False)
class ComputeDomain(ModelDomain):
    """Compute model data."""


@dataclass(repr=False)
class ApplicationDomain(ModelDomain):
    """Application model data."""


@dataclass
class PlatformModel:
    """The complete platform model, grouped by domain."""

    platform: PlatformDomain = field(default_factory=PlatformDomain)
    network: NetworkDomain = field(default_factory=NetworkDomain)
    compute: ComputeDomain = field(default_factory=ComputeDomain)
    application: ApplicationDomain = field(default_factory=ApplicationDomain)
