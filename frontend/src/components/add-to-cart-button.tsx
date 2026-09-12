"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Check, LoaderCircle, ShoppingCart } from "lucide-react";
import { useCart } from "@/components/cart-provider";
import { Button } from "@/components/ui/button";
import type { Product } from "@/lib/catalog";

export function AddToCartButton(props: {
  product: Product;
  compact?: boolean;
}) {
  const cart = useCart();
  return (
    <AddToCartControl
      key={cart.state.status === "ready" ? cart.state.owner : cart.state.status}
      {...props}
    />
  );
}

function AddToCartControl({
  product,
  compact = false,
}: {
  product: Product;
  compact?: boolean;
}) {
  const cart = useCart();
  const [added, setAdded] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );
  const pending = Boolean(cart.pending[product.id]);
  const error = cart.errors[product.id];
  const outOfStock = product.stock === 0;

  if (cart.state.status === "loading") {
    return (
      <Button
        disabled
        aria-busy="true"
        className={compact ? "h-10" : "h-12 w-full"}
      >
        Loading…
      </Button>
    );
  }

  if (cart.state.status === "guest") {
    return (
      <Button asChild className={compact ? "h-10" : "h-12 w-full"}>
        <Link href="/login" prefetch={false}>
          <ShoppingCart aria-hidden="true" />
          Sign in to add
        </Link>
      </Button>
    );
  }

  if (cart.state.status === "error") {
    return (
      <div className="space-y-2">
        <Button
          onClick={() => cart.refresh()}
          variant="outline"
          className={compact ? "h-10" : "h-12 w-full"}
        >
          Try again
        </Button>
        <p role="alert" className="text-xs text-muted-foreground">
          Your cart is temporarily unavailable.
        </p>
      </div>
    );
  }

  async function add() {
    setAdded(false);
    const ok = await cart.addItem(product.id);
    if (ok) {
      setAdded(true);
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => setAdded(false), 4000);
    }
  }

  return (
    <div
      className="space-y-2"
      data-cart-private
      onFocusCapture={(event) => {
        if (cart.concealed) event.target.blur();
      }}
      aria-hidden={cart.concealed || undefined}
      style={{ opacity: cart.concealed ? 0 : 1 }}
    >
      <Button
        onClick={() => void add()}
        disabled={pending || outOfStock || cart.readOnly}
        aria-busy={pending}
        className={compact ? "h-10" : "h-12 w-full"}
      >
        {pending ? (
          <LoaderCircle
            className="size-4 animate-spin motion-reduce:animate-none"
            aria-hidden="true"
          />
        ) : added ? (
          <Check aria-hidden="true" />
        ) : (
          <ShoppingCart aria-hidden="true" />
        )}
        {outOfStock
          ? "Out of stock"
          : pending
            ? "Adding…"
            : added
              ? "Saved to cart"
              : "Add to cart"}
      </Button>
      {added && !error && (
        <p role="status" className="text-xs">
          Saved.{" "}
          <a href="/cart" className="underline underline-offset-4">
            View your cart
          </a>
          .
        </p>
      )}
      {error && (
        <p role="alert" className="text-xs text-destructive">
          {error}{" "}
          {error.includes("session") ? (
            <Link href="/login" className="underline underline-offset-4">
              Sign in
            </Link>
          ) : null}
        </p>
      )}
      {outOfStock && !error && (
        <p className="text-xs text-muted-foreground">
          This object is currently out of stock.
        </p>
      )}
    </div>
  );
}
