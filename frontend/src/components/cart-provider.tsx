"use client";

import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  useTransition,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { changeCart } from "@/app/cart/actions";
import type { CartChange, CartSnapshot, CartFailure } from "@/lib/cart-state";
export type { Cart, CartItem } from "@/lib/cart-state";

type CartContextValue = {
  state: CartSnapshot | { status: "loading" };
  count: number;
  concealed: boolean;
  pending: Record<number, boolean>;
  errors: Record<number, string>;
  readOnly: boolean;
  staleNotice: string;
  refresh: () => void;
  setQuantity: (productId: number, quantity: number) => Promise<boolean>;
  stepQuantity: (productId: number, delta: -1 | 1) => Promise<boolean>;
  removeItem: (productId: number) => Promise<boolean>;
  addItem: (productId: number) => Promise<boolean>;
  clearError: (productId: number) => void;
};
const subscribe = () => () => {};
const CartContext = createContext<CartContextValue | null>(null);
export function useCart() {
  const value = useContext(CartContext);
  if (!value) throw new Error("Cart controls require CartProvider");
  return value;
}

// Server props are authoritative. This provider only coordinates interactive
// controls; Next owns reads, action dispatch and refreshed server rendering.
export function CartProvider({
  snapshot,
  children,
}: {
  snapshot: CartSnapshot;
  children: ReactNode;
}) {
  const router = useRouter();
  const hydrated = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
  const [refreshing, startRefresh] = useTransition();
  const [mutating, startMutation] = useTransition();
  const [pending, setPending] = useState<Record<number, boolean>>({});
  const busy = useRef(new Set<number>());
  const [errors, setErrors] = useState<Record<number, CartFailure>>({});
  const [concealed, setConcealed] = useState(false);
  const [previous, setPrevious] = useState(snapshot);
  const [lastReady, setLastReady] = useState(
    snapshot.status === "ready" ? snapshot : null,
  );
  if (snapshot !== previous) {
    setPrevious(snapshot);
    setConcealed(false);
    // The server keys this provider by verified owner; unknown/different
    // identities remount it, so a fallback never crosses accounts.
    if (snapshot.status === "ready") setLastReady(snapshot);
  }
  // A completed Next transition has applied the action's refreshed server tree.
  // A successful read settles uncertainty even if the write response was lost.
  if (
    !mutating &&
    !refreshing &&
    snapshot.status === "ready" &&
    Object.values(errors).some((failure) => failure.uncertain)
  ) {
    setErrors(
      Object.fromEntries(
        Object.entries(errors).filter(([, failure]) => !failure.uncertain),
      ),
    );
  }
  useEffect(() => {
    // Another visible window can change the cookie without a hide event.
    // Conceal private data until the server verifies the returning identity.
    function refresh() {
      hide();
      startRefresh(() => router.refresh());
    }
    function hide() {
      const active = document.activeElement;
      if (
        active instanceof HTMLElement &&
        active.closest("[data-cart-private]")
      )
        active.blur();
      setConcealed(true);
    }
    function visible() {
      if (document.visibilityState === "visible") refresh();
      else hide();
    }
    window.addEventListener("focus", refresh);
    window.addEventListener("pageshow", refresh);
    window.addEventListener("pagehide", hide);
    document.addEventListener("visibilitychange", visible);
    return () => {
      window.removeEventListener("focus", refresh);
      window.removeEventListener("pageshow", refresh);
      window.removeEventListener("pagehide", hide);
      document.removeEventListener("visibilitychange", visible);
    };
  }, [router]);

  function clearError(productId: number) {
    setErrors((current) => {
      const next = { ...current };
      delete next[productId];
      return next;
    });
  }
  function mutate(change: CartChange): Promise<boolean> {
    if (snapshot.status !== "ready" || busy.current.has(change.productId))
      return Promise.resolve(false);
    busy.current.add(change.productId);
    setPending((current) => ({ ...current, [change.productId]: true }));
    clearError(change.productId);
    return new Promise((resolve) => {
      startMutation(async () => {
        try {
          const result = await changeCart(snapshot.owner, change);
          if (!result.ok)
            setErrors((current) => ({
              ...current,
              [change.productId]: result,
            }));
          resolve(result.ok);
        } catch {
          setErrors((current) => ({
            ...current,
            [change.productId]: {
              error:
                "We couldn't confirm the change. Refresh your cart before trying again.",
              uncertain: true,
            },
          }));
          // Transport failures can happen after a committed write. Never retry
          // an add automatically: ask Next for the authoritative server view.
          startRefresh(() => router.refresh());
          resolve(false);
        } finally {
          busy.current.delete(change.productId);
          setPending((current) => {
            const next = { ...current };
            delete next[change.productId];
            return next;
          });
        }
      });
    });
  }
  const stale =
    snapshot.status === "error" && lastReady?.owner === snapshot.owner
      ? lastReady
      : null;
  const state = stale ?? snapshot;
  return (
    <CartContext.Provider
      value={{
        state,
        concealed,
        count:
          state.status === "ready"
            ? state.cart.items.reduce((sum, item) => sum + item.quantity, 0)
            : 0,
        pending,
        errors: Object.fromEntries(
          Object.entries(errors).map(([id, failure]) => [id, failure.error]),
        ),
        readOnly:
          !hydrated ||
          Boolean(stale) ||
          Object.values(errors).some((failure) => failure.uncertain),
        staleNotice:
          stale || Object.values(errors).some((failure) => failure.uncertain)
            ? "Couldn't update your cart. Please try again."
            : "",
        refresh: () => {
          setErrors({});
          startRefresh(() => router.refresh());
        },
        setQuantity: (productId, quantity) =>
          mutate({ kind: "set", productId, quantity }),
        stepQuantity: (productId, delta) =>
          mutate({ kind: "step", productId, delta }),
        addItem: (productId) => mutate({ kind: "add", productId }),
        removeItem: (productId) => mutate({ kind: "remove", productId }),
        clearError,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}
