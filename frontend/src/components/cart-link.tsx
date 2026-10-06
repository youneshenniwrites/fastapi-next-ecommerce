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
  return (
    <a
      href="/cart"
      aria-label={label}
      className={classes}
      onClick={onClick}
      onPointerDown={(event) => {
        // The streamed header is replaced when the cart snapshot arrives. A
        // click that lands during that swap never finishes, so start the
        // full navigation at press time. Modified clicks keep native behavior.
        if (
          event.button !== 0 ||
          event.metaKey ||
          event.ctrlKey ||
          event.shiftKey ||
          event.altKey
        )
          return;
        window.location.assign("/cart");
      }}
    >
      {content}
    </a>
  );
}
