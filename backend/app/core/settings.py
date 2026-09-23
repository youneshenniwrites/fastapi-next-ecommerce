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

    STRIPE_ENABLED: bool = False
    STRIPE_API_KEY: SecretStr = SecretStr("")
    STRIPE_WEBHOOK_SECRET: SecretStr = SecretStr("")
    STRIPE_CHECKOUT_ORIGIN: str = ""

    @model_validator(mode="after")
    def sandbox_payments(self) -> "Settings":
        """Fail closed on live keys or incomplete explicitly enabled configuration."""
        from urllib.parse import urlsplit

        key = self.STRIPE_API_KEY.get_secret_value()
        if key and not key.startswith(("rk_test_", "sk_test_")):
            raise ValueError("Only Stripe test-mode keys are allowed")
        if self.STRIPE_ENABLED:
            origin = urlsplit(self.STRIPE_CHECKOUT_ORIGIN)
            if (
                not key
                or not self.STRIPE_WEBHOOK_SECRET.get_secret_value().startswith(
                    "whsec_"
                )
                or origin.username
                or origin.password
                or origin.query
                or origin.fragment
                or origin.path not in ("", "/")
                or not origin.hostname
                or (
                    origin.scheme != "https"
                    and not (
                        origin.scheme == "http"
                        and origin.hostname in ("localhost", "127.0.0.1")
                    )
                )
            ):
                raise ValueError(
                    "Sandbox payments require test credentials and an exact trusted storefront origin"
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
