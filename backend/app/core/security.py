from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.settings import settings


class LegacyBcryptHasher(BcryptHasher):
    def verify(self, password: str | bytes, hash: str | bytes) -> bool:
        # Passlib historically truncated bcrypt passwords at 72 bytes. Preserve
        # that behavior only for verification; rehash the full password in Argon2.
        encoded = password.encode("utf-8") if isinstance(password, str) else password
        return super().verify(encoded[:72], hash)


# New passwords use Argon2; existing bcrypt hashes upgrade after a successful login.
password_hash = PasswordHash((Argon2Hasher(), LegacyBcryptHasher()))
ALGORITHM = "HS256"
DUMMY_HASH = password_hash.hash("unused-password-for-timing")


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(subject: int, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)
    lifetime = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return jwt.encode(
        {"sub": str(subject), "iat": now, "exp": now + lifetime},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"require": ["sub", "exp", "iat"]},
    )
