from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """HTTP errors use a detail string; validation errors have FastAPI's 422 schema."""

    detail: str
