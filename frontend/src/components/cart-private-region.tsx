"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useCart } from "@/components/cart-provider";

// Keep an already-started pointer activation alive, then let native inert
// remove the entire concealed subtree from keyboard and pointer interaction.
export function CartPrivateRegion({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  const { concealed } = useCart();
  const [activating, setActivating] = useState(false);
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    function finish() {
      clearTimeout(timer);
      // click follows pointerup; applying inert earlier would swallow that click.
      timer = setTimeout(() => setActivating(false), 0);
    }
    window.addEventListener("pointerup", finish);
    window.addEventListener("pointercancel", finish);
    window.addEventListener("blur", finish);
    window.addEventListener("pagehide", finish);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("pointerup", finish);
      window.removeEventListener("pointercancel", finish);
      window.removeEventListener("blur", finish);
      window.removeEventListener("pagehide", finish);
    };
  }, []);
  return (
    <div
      className={className}
      data-cart-private
      onPointerDownCapture={(event) => {
        if (event.button === 0) setActivating(true);
      }}
      inert={concealed && !activating}
      aria-hidden={concealed || undefined}
      style={{ opacity: concealed ? 0 : 1 }}
    >
      {children}
    </div>
  );
}
