class DependencyError(Exception):
    """Generic dependency error."""


class UnsupportedDependencyInterfaceError(DependencyError):
    """The interface is not supported by this library."""


class DependencyResolutionError(DependencyError):
    """Dependencies could not be resolved."""
