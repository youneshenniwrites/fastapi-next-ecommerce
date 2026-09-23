"""Operator-invoked bounded reconciliation; never schedules background work."""

import argparse

from fastapi import HTTPException
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.order import Order
from app.services.payments import (
    reconcile_known_session,
    reconcile_payment,
    reconcile_unknown_session,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--after-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=50, choices=range(1, 101))
    parser.add_argument("--order-id", type=int)
    parser.add_argument(
        "--session-id", help="Known test session for recovery; never creates a session"
    )
    parser.add_argument(
        "--verify-absent-session",
        action="store_true",
        help="After expiry, scan up to 1000 provider sessions before releasing an unbound intent",
    )
    args = parser.parse_args()
    if bool(args.order_id) != bool(args.session_id or args.verify_absent_session) or (
        args.session_id and args.verify_absent_session
    ):
        parser.error(
            "Supply --order-id with exactly one of --session-id or --verify-absent-session"
        )
    with SessionLocal() as db:
        if args.order_id:
            try:
                order = (
                    reconcile_unknown_session(db, args.order_id)
                    if args.verify_absent_session
                    else reconcile_known_session(db, args.order_id, args.session_id)
                )
                print(f"Order {order.id}: {order.payment_status}")
            except HTTPException as exc:
                print(f"Order {args.order_id}: unresolved ({exc.status_code})")
                raise SystemExit(1) from None
            return
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
