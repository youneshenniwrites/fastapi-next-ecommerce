from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """HTTP errors use a detail string; validation errors have FastAPI's 422 schema."""

    detail: str


RATE_LIMITED_RESPONSE = {
    429: {
        "model": ErrorResponse,
        "description": "Too many requests. Retry after the Retry-After delay (seconds).",
        "headers": {
            "Retry-After": {
                "description": "Seconds until the current window expires.",
                "schema": {"type": "integer", "minimum": 1},
            },
            "X-RateLimit-Limit": {
                "description": "Request limit for the current window.",
                "schema": {"type": "integer"},
            },
            "X-RateLimit-Remaining": {
                "description": "Requests remaining in the current window.",
                "schema": {"type": "integer"},
            },
        },
    }
}
