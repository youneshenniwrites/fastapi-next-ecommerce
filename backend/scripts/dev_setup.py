"""Generate local credentials once; never overwrite an existing environment."""

import os
import secrets
from pathlib import Path


def main():
    path = Path(__file__).resolve().parents[1] / ".env"
    password = secrets.token_hex(24)
    content = (
        f"POSTGRES_PASSWORD={password}\n"
        f"DATABASE_URL=postgresql+psycopg://ecommerce:{password}@localhost:5432/ecommerce\n"
        f"SECRET_KEY={secrets.token_hex(32)}\n"
    )
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print("Existing backend/.env preserved")
        return
    with os.fdopen(fd, "w") as file:
        file.write(content)
    print("Created backend/.env with local-only credentials")


if __name__ == "__main__":
    main()
