class OtasError(Exception):
    """Base exception for all OTAS errors."""


class OtasAuthenticationError(OtasError):
    """Raised when SDK key authentication fails."""


class OtasConfigurationError(OtasError):
    """Raised when the SDK is misconfigured."""