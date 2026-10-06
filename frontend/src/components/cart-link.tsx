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
        // mouse click that lands during that swap never finishes, so a mouse
        // press starts the navigation. Touch contact is not activation: a
        // finger can still scroll or long-press. If that gesture ends after
        // the header was replaced, finish it from the window.
        if (
          event.button !== 0 ||
          event.metaKey ||
          event.ctrlKey ||
          event.shiftKey ||
          event.altKey
        )
          return;
        if (event.pointerType === "mouse") {
          window.location.assign("/cart");
          return;
        }
        const link = event.currentTarget;
        const pointerId = event.pointerId;
        const startX = event.clientX;
        const startY = event.clientY;
        const finish = (end: PointerEvent) => {
          if (end.pointerId !== pointerId) return;
          window.removeEventListener("pointerup", finish);
          window.removeEventListener("pointercancel", finish);
          if (end.type === "pointercancel") return;
          if (Math.hypot(end.clientX - startX, end.clientY - startY) > 10)
            return;
          if (link.isConnected) return;
          window.location.assign("/cart");
        };
        window.addEventListener("pointerup", finish);
        window.addEventListener("pointercancel", finish);
      }}
    >
      {content}
    </a>
  );
}
