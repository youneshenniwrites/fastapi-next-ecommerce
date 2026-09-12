"use client";

import { AlertTriangle } from "lucide-react";
import { useCart } from "@/components/cart-provider";
import { Button } from "@/components/ui/button";

export function CartRefreshWarning() {
  const cart = useCart();
  if (cart.state.status !== "ready" || !cart.staleNotice) return null;
  return (
    <div
      role="status"
      className="mx-auto my-4 max-w-7xl flex flex-wrap items-center gap-2 rounded-md border border-border bg-secondary p-4 text-sm"
    >
      <AlertTriangle className="size-4 shrink-0" aria-hidden="true" />
      <span>{cart.staleNotice}</span>
      <Button type="button" variant="outline" size="sm" onClick={cart.refresh}>
        Refresh cart
      </Button>
    </div>
  );
}
