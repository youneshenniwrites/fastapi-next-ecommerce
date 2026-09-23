"""Operator-invoked bounded reconciliation; never schedules background work."""

import argparse

from fastapi import HTTPException
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.order import Order
from app.services.payments import reconcile_payment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--after-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=50, choices=range(1, 101))
    args = parser.parse_args()
    with SessionLocal() as db:
        ids = list(
            db.scalars(
                select(Order.id)
                .where(Order.payment_status == "pending", Order.id > args.after_id)
                .order_by(Order.id)
                .limit(args.limit)
            )
        )
        db.commit()
        for order_id in ids:
            try:
                order = reconcile_payment(db, None, order_id)
                print(f"Order {order_id}: {order.payment_status}")
            except HTTPException as exc:
                print(f"Order {order_id}: unresolved ({exc.status_code})")
        if ids:
            print(f"Next cursor: --after-id {ids[-1]}")


if __name__ == "__main__":
    main()
