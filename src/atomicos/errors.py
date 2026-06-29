"""Recoverable domain errors surfaced to the UI."""


class AtomicOSError(Exception):
    """Base error for failures that should be shown as concise user logs."""


class ConfigurationError(AtomicOSError):
    """Raised when runtime configuration is missing or unusable."""


class InferenceError(AtomicOSError):
    """Raised when remote synthesis fails or returns unusable data."""


class PersistenceError(AtomicOSError):
    """Raised when note persistence to Obsidian fails."""


class ValidationError(AtomicOSError):
    """Raised when user-provided workflow input is incomplete or invalid."""
