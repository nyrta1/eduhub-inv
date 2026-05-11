from __future__ import annotations

ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    400: {
        "description": "Bad request (invalid business input).",
        "content": {
            "application/json": {
                "example": {
                    "detail": {"code": "password_policy", "message": "Password is too weak."},
                    "request_id": "ab84e9f7-78f7-4556-9163-f18a25ddf9ef",
                },
            },
        },
    },
    401: {
        "description": "Authentication required or token invalid/expired.",
        "content": {
            "application/json": {
                "example": {
                    "detail": {
                        "code": "invalid_token",
                        "message": "Invalid or expired access token.",
                    },
                    "request_id": "ab84e9f7-78f7-4556-9163-f18a25ddf9ef",
                },
            },
        },
    },
    403: {
        "description": "Authenticated but missing role/permission or ownership scope.",
        "content": {
            "application/json": {
                "example": {
                    "detail": {"code": "forbidden", "message": "Insufficient permissions."},
                    "request_id": "ab84e9f7-78f7-4556-9163-f18a25ddf9ef",
                },
            },
        },
    },
    404: {
        "description": "Requested resource not found.",
        "content": {
            "application/json": {
                "example": {
                    "detail": {"code": "not_found", "message": "Resource not found."},
                    "request_id": "ab84e9f7-78f7-4556-9163-f18a25ddf9ef",
                },
            },
        },
    },
    409: {
        "description": "Conflict with current resource state.",
        "content": {
            "application/json": {
                "example": {
                    "detail": {"code": "conflict", "message": "Resource already exists."},
                    "request_id": "ab84e9f7-78f7-4556-9163-f18a25ddf9ef",
                },
            },
        },
    },
    422: {
        "description": "Validation error; malformed or out-of-contract request.",
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "code": "validation_error",
                        "message": "Request validation failed",
                        "request_id": "ab84e9f7-78f7-4556-9163-f18a25ddf9ef",
                    },
                },
            },
        },
    },
    429: {
        "description": "Rate limit exceeded on a protected endpoint.",
        "content": {
            "application/json": {
                "example": {
                    "detail": {"code": "rate_limited", "message": "Too many requests."},
                    "request_id": "ab84e9f7-78f7-4556-9163-f18a25ddf9ef",
                },
            },
        },
    },
    500: {
        "description": "Unexpected internal error (sanitized payload).",
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "code": "internal_error",
                        "message": "Unexpected server error",
                        "reference_id": "fbb8db00-4f8d-4caf-a5c7-f6824c41a793",
                        "request_id": "ab84e9f7-78f7-4556-9163-f18a25ddf9ef",
                    },
                },
            },
        },
    },
}
