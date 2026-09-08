from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Lifetime in seconds; derived from the issued token configuration.


class TokenPayload(BaseModel):
    sub: str  # user id
