"""Shared routing utilities and response metadata."""

from ..models import ErrorResponse

COMMON_ERROR_RESPONSES = {
    400: {
        "model": ErrorResponse,
        "description": "Invalid request",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid request", "code": "invalid_request"}
            }
        },
    },
    401: {
        "model": ErrorResponse,
        "description": "Missing or invalid API key",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Not authenticated",
                    "code": "not_authenticated",
                }
            }
        },
    },
    403: {
        "model": ErrorResponse,
        "description": "Forbidden",
        "content": {
            "application/json": {
                "example": {"detail": "Not authorized", "code": "not_authorized"}
            }
        },
    },
    500: {
        "model": ErrorResponse,
        "description": "Server error",
        "content": {
            "application/json": {
                "example": {"detail": "Server error", "code": "server_error"}
            }
        },
    },
}

__all__ = ["COMMON_ERROR_RESPONSES"]