"""Stable sanitized REST error mapping."""

from fastapi.responses import JSONResponse

from app.codex.exceptions import (
    AdapterStateError,
    ExecutableNotFound,
    ProcessCommunicationFailed,
    ProcessStartFailed,
    ProcessStopFailed,
)
from app.services.auth import (
    LoginAlreadyPending,
    LoginCancellationFailed,
    LoginNotPending,
)


def error_response(error: Exception) -> JSONResponse:
    """Map internal failures without using their potentially private text."""

    if isinstance(error, ExecutableNotFound):
        code, message, status = "CODEX_NOT_INSTALLED", "Codex is not installed", 503
    elif isinstance(error, ProcessStartFailed):
        code, message, status = "CODEX_START_FAILED", "Codex failed to start", 503
    elif isinstance(error, LoginAlreadyPending):
        code, message, status = "CODEX_LOGIN_PENDING", "Login is already pending", 409
    elif isinstance(error, LoginNotPending):
        code, message, status = "CODEX_NOT_AUTHENTICATED", "Login is not pending", 409
    elif isinstance(error, LoginCancellationFailed):
        code, message, status = "CODEX_PROTOCOL_ERROR", "Login cancellation failed", 502
    elif isinstance(error, AdapterStateError):
        code, message, status = "UPSTREAM_UNAVAILABLE", "Codex is unavailable", 503
    elif isinstance(error, (ProcessCommunicationFailed, ProcessStopFailed)):
        code, message, status = "CODEX_PROTOCOL_ERROR", "Codex protocol error", 502
    else:
        code, message, status = "INTERNAL_ERROR", "Internal error", 500
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message}},
    )
