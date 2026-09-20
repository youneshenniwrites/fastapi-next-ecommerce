from pathlib import Path

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str = Field(min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, gt=0)
    RATE_LIMIT_PROXY_SECRET: SecretStr = SecretStr("")
    RATE_LIMIT_AUTH_REGISTER: int = Field(default=60, gt=0)
    RATE_LIMIT_AUTH_LOGIN: int = Field(default=60, gt=0)
    RATE_LIMIT_WRITE: int = Field(default=300, gt=0)

    @field_validator("RATE_LIMIT_PROXY_SECRET")
    @classmethod
    def valid_proxy_secret(cls, value: SecretStr) -> SecretStr:
        """Allow disabled signing or a dedicated sufficiently long key."""
        raw = value.get_secret_value()
        if raw and (len(raw) < 32 or raw != raw.strip()):
            raise ValueError(
                "proxy signing key must contain at least 32 characters without surrounding whitespace"
            )
        return value

    @model_validator(mode="after")
    def dedicated_proxy_key(self) -> "Settings":
        """Prevent reuse of the authentication signing key for proxy assertions."""
        if self.RATE_LIMIT_PROXY_SECRET.get_secret_value() == self.SECRET_KEY:
            raise ValueError(
                "proxy signing key must be separate from authentication key"
            )
        return self

    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "local"
    SENTRY_RELEASE: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1, ge=0.0, le=1.0)

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
        hide_input_in_errors=True,
    )


settings = Settings()
