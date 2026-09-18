"""Controlled exceptions for the Codex process boundary."""


class ExecutableNotFound(Exception):
    """The configured Codex executable could not be resolved."""


class ProcessStartFailed(Exception):
    """The Codex app-server process could not be started or was already started."""


class ProcessStopFailed(Exception):
    """The Codex app-server child did not exit after bounded cleanup attempts."""


class ProcessCommunicationFailed(Exception):
    """A controlled failure occurred while communicating with the child."""
