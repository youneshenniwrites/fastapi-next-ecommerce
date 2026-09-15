from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """HTTP errors use a detail string; validation errors have FastAPI's 422 schema."""

    detail: str


RATE_LIMITED_RESPONSE = {
    429: {
        "model": ErrorResponse,
        "description": "Too many requests. Retry after the Retry-After delay (seconds).",
    }
}
