"use client";

import { ShoppingBag } from "lucide-react";
import { useCart } from "@/components/cart-provider";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function CartLink({
  className,
  onClick,
}: {
  className?: string;
  onClick?: () => void;
}) {
  const cart = useCart();
  const count = cart.count;
  const label =
    cart.state.status === "ready" && !cart.concealed && count > 0
      ? `Cart, ${count} ${count === 1 ? "item" : "items"}`
      : "Cart";
  const content = (
    <>
      <ShoppingBag className="size-4" aria-hidden="true" />
      <span>Cart</span>
      {cart.state.status === "loading" ? (
        <span className="sr-only">(loading)</span>
      ) : cart.state.status === "ready" && count > 0 ? (
        <Badge
          aria-hidden={cart.concealed || undefined}
          style={{ opacity: cart.concealed ? 0 : 1 }}
          variant="secondary"
          data-testid="cart-count"
          className="rounded-md px-1.5 py-0.5 text-[10px] leading-none"
        >
          {count > 99 ? "99+" : count}
        </Badge>
      ) : null}
    </>
  );
  const classes = cn("inline-flex items-center gap-2", className);
  // Always a full navigation. Swapping this control to a client Link while the
  // cart is loading drops a click that lands as the header refreshes after sign-in.
  return (
    <a href="/cart" aria-label={label} className={classes} onClick={onClick}>
      {content}
    </a>
  );
}
