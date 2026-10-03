"""Private subprocess fixture for the disposable restore rehearsal."""

import hashlib
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from alembic import command

endpoint = urlsplit(os.environ["DATABASE_URL"])
if (
    endpoint.scheme != "postgresql+psycopg"
    or endpoint.hostname != "127.0.0.1"
    or endpoint.username != "postgres"
    or endpoint.path != "/rehearsal"
    or endpoint.query
    or endpoint.fragment
):
    raise RuntimeError("Only the disposable loopback rehearsal database is accepted")

from app.core import settings as configuration  # noqa: E402

# Override the fixed .env loader before importing application/database modules.
# No inherited telemetry, payment, diagnostic or proxy configuration is used.
configuration.settings = configuration.Settings(
    _env_file=None,
    DATABASE_URL=os.environ["DATABASE_URL"],
    SECRET_KEY=os.environ["SECRET_KEY"],
)

from fastapi.testclient import TestClient  # noqa: E402

from app.bootstrap import seed_demo  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

PASSWORD = "FictionalRestore123!"
EMAILS = ["restore-a@example.com", "restore-b@example.com"]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def snapshot():
    """Compare every table and sequence, without retaining plaintext rows."""
    tables = {}
    quote = engine.dialect.identifier_preparer.quote
    with engine.connect() as connection:
        for name in sorted(inspect(connection).get_table_names()):
            rows = (
                connection.execute(
                    text(
                        f"SELECT row_to_json(t)::text FROM {quote(name)} t ORDER BY row_to_json(t)::text"
                    )
                )
                .scalars()
                .all()
            )
            tables[name] = {
                "rows": len(rows),
                "sha256": hashlib.sha256(json.dumps(rows).encode()).hexdigest(),
            }
        sequences = {}
        for name in inspect(connection).get_sequence_names():
            sequences[name] = list(
                connection.execute(
                    text(f"SELECT last_value, is_called FROM {quote(name)}")
                ).one()
            )
    return {"tables": tables, "sequences": sequences}


def request(client, method, path, status=200, **kwargs):
    response = client.request(method, path, **kwargs)
    require(response.status_code == status, f"Unexpected response for {method} {path}")
    return response.json() if response.content else None


def login(client, email, password=PASSWORD, status=200):
    result = request(
        client,
        "POST",
        "/api/v1/auth/login",
        status,
        data={"username": email, "password": password},
    )
    return (
        {"Authorization": f"Bearer {result['access_token']}"} if status == 200 else None
    )


def run(mode, path):
    config = Config("alembic.ini")
    if mode == "empty":
        require(
            not inspect(engine).get_table_names(), "Failed restore left partial tables"
        )
        return {"empty": True}
    if mode == "seed":
        command.upgrade(config, "head")
        with SessionLocal() as db:
            seed_demo(db)
            db.commit()
    command.check(config)
    with engine.connect() as connection:
        head = connection.scalar(text("SELECT version_num FROM alembic_version"))
    require(
        head == ScriptDirectory.from_config(config).get_current_head(),
        "Migration head mismatch",
    )
    expected = None
    if mode == "verify":
        expected = json.loads(path.read_text())
        require(snapshot() == expected["snapshot"], "Restored rows/sequences differ")
    with TestClient(app) as client:
        if mode == "seed":
            for email in EMAILS:
                request(
                    client,
                    "POST",
                    "/api/v1/auth/register",
                    201,
                    json={"email": email, "password": PASSWORD},
                )
        owners = [login(client, email) for email in EMAILS]
        catalog = request(client, "GET", "/api/v1/products/?limit=100")
        require(len(catalog) == 12, "Expected fictional twelve-product catalog")
        if mode == "seed":
            orders = []
            for index, headers in enumerate(owners):
                product = catalog[index]
                request(
                    client,
                    "PUT",
                    f"/api/v1/cart/items/{product['id']}",
                    headers=headers,
                    json={"quantity": 2},
                )
                order = request(
                    client,
                    "POST",
                    "/api/v1/orders/drafts",
                    201,
                    headers=headers,
                    json={"lines": [{"product_id": product["id"], "quantity": 2}]},
                )
                if index == 0:
                    order = request(
                        client,
                        "POST",
                        f"/api/v1/orders/{order['id']}/place",
                        headers={**headers, "Idempotency-Key": "restore-order-a"},
                    )
                orders.append(order)
                request(
                    client,
                    "PUT",
                    f"/api/v1/cart/items/{product['id']}",
                    headers=headers,
                    json={"quantity": index + 1},
                )
            expected = {
                "snapshot": snapshot(),
                "orders": orders,
                "catalog": request(client, "GET", "/api/v1/products/?limit=100"),
                "carts": [
                    request(client, "GET", "/api/v1/cart/", headers=h) for h in owners
                ],
            }
            path.write_text(json.dumps(expected))
        else:
            expected = json.loads(path.read_text())
            require(
                snapshot() == expected["snapshot"], "Restored rows/sequences differ"
            )
            require(catalog == expected["catalog"], "Restored catalog differs")
            for index, headers in enumerate(owners):
                require(
                    request(client, "GET", "/api/v1/auth/me", headers=headers)["email"]
                    == EMAILS[index],
                    "Restored authentication owner differs",
                )
                login(client, EMAILS[index], "WrongPassword!", 401)
                require(
                    request(client, "GET", "/api/v1/cart/", headers=headers)
                    == expected["carts"][index],
                    "Restored cart differs",
                )
                require(
                    request(client, "GET", "/api/v1/orders/", headers=headers)
                    == [expected["orders"][index]],
                    "Restored owned order list differs",
                )
                request(
                    client,
                    "GET",
                    f"/api/v1/orders/{expected['orders'][1 - index]['id']}",
                    404,
                    headers=headers,
                )
            # Exercise restored sequences with actual writes after the comparison.
            user = request(
                client,
                "POST",
                "/api/v1/auth/register",
                201,
                json={"email": "restore-new@example.com", "password": PASSWORD},
            )
            require(user["id"] > 2, "Restored user sequence did not advance")
            order = request(
                client,
                "POST",
                "/api/v1/orders/drafts",
                201,
                headers=owners[0],
                json={"lines": [{"product_id": catalog[0]["id"], "quantity": 1}]},
            )
            require(
                order["id"] > max(o["id"] for o in expected["orders"]),
                "Order sequence did not advance",
            )
    engine.dispose()
    return {
        "migration_head": head,
        "tables": expected["snapshot"]["tables"],
        "api_smoke": (
            "catalog, password login, carts, draft/placed orders and account isolation passed"
            if mode == "verify"
            else "fictional catalog/customers/carts/orders created"
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1], Path(sys.argv[2]))))
