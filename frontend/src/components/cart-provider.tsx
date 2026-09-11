"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { components } from "@/lib/api/schema";
import { useSession } from "@/components/session-provider";

export type Cart = components["schemas"]["CartRead"];
export type CartItem = components["schemas"]["CartItem"];

type CartSnapshot =
  | { status: "loading" }
  | { status: "guest" }
  | { status: "error" }
  | { status: "ready"; cart: Cart };

type CartContextValue = {
  state: CartSnapshot;
  count: number;
  pending: Record<number, boolean>;
  errors: Record<number, string>;
  notice: string;
  refresh: () => void;
  setQuantity: (productId: number, quantity: number) => Promise<boolean>;
  removeItem: (productId: number) => Promise<boolean>;
  addItem: (productId: number) => Promise<boolean>;
  clearError: (productId: number) => void;
};

const CartContext = createContext<CartContextValue>({
  state: { status: "loading" },
  count: 0,
  pending: {},
  errors: {},
  notice: "",
  refresh: () => {},
  setQuantity: async () => false,
  removeItem: async () => false,
  addItem: async () => false,
  clearError: () => {},
});

export function useCart() {
  return useContext(CartContext);
}

function cartCount(cart: Cart | null) {
  if (!cart) return 0;
  return cart.items.reduce((total, item) => total + item.quantity, 0);
}

function errorMessage(status: number, body: unknown) {
  if (body && typeof body === "object") {
    const detail = (body as { error?: unknown }).error;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  if (status === 401) return "Your session expired. Sign in to continue.";
  if (status === 404) return "This product is no longer available.";
  if (status === 409)
    return "Not enough stock for that quantity. Stock is not reserved.";
  if (status === 422) return "Quantity must be a whole number from 1 to 99.";
  return "Your cart is temporarily unavailable. Please try again.";
}

// Private cart state lives only in memory. It is fetched with cookies through
// the same-origin handler; bearer tokens are never exposed to the browser.
export function CartProvider({ children }: { children: ReactNode }) {
  const session = useSession();
  const [snapshot, setSnapshot] = useState<CartSnapshot | undefined>();
  const [pending, setPending] = useState<Record<number, boolean>>({});
  const [errors, setErrors] = useState<Record<number, string>>({});
  const [notice, setNotice] = useState("");
  const requestId = useRef(0);
  const busy = useRef(new Set<number>());
  const lastEmail = useRef<string | null>(null);
  const sessionRef = useRef(session);
  const snapshotRef = useRef<CartSnapshot | undefined>(undefined);

  useEffect(() => {
    sessionRef.current = session;
  }, [session]);

  useEffect(() => {
    snapshotRef.current = snapshot;
  }, [snapshot]);

  const applySnapshot = useCallback((id: number, next: CartSnapshot) => {
    if (requestId.current === id) setSnapshot(next);
  }, []);

  // Background failures preserve a rendered cart and surface a retry notice
  // instead of wiping private UI; explicit loads without a cart still fail
  // into the error state with its Try again action.
  const markStale = useCallback((id: number) => {
    if (requestId.current !== id) return;
    if (snapshotRef.current?.status === "ready") {
      setNotice("Couldn't update your cart. Please try again.");
      return;
    }
    setSnapshot({ status: "error" });
  }, []);

  const fetchCart = useCallback(
    async (id: number, signal: AbortSignal) => {
      try {
        const response = await fetch("/api/cart", {
          cache: "no-store",
          signal: AbortSignal.any([signal, AbortSignal.timeout(10000)]),
        });
        if (signal.aborted) return;
        if (response.status === 401) {
          applySnapshot(id, { status: "guest" });
          return;
        }
        if (!response.ok) {
          markStale(id);
          return;
        }
        const cart = (await response.json()) as Cart;
        applySnapshot(id, { status: "ready", cart });
      } catch {
        if (!signal.aborted) markStale(id);
      }
    },
    [applySnapshot, markStale],
  );

  // Authoritative re-read after writes settle. Concurrent per-product
  // mutations and refreshes can each land a snapshot that predates a
  // settled write, so the last mutation to finish re-reads the server cart
  // instead of trusting any in-flight response.
  const reconcile = useCallback(async () => {
    const current = sessionRef.current;
    if (current.status !== "authenticated") return;
    const id = ++requestId.current;
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 10000);
    try {
      await fetchCart(id, controller.signal);
    } finally {
      window.clearTimeout(timer);
    }
  }, [fetchCart]);

  const refresh = useCallback(() => {
    const current = sessionRef.current;
    if (current.status === "loading") {
      requestId.current += 1;
      setSnapshot({ status: "loading" });
      return;
    }
    if (current.status !== "authenticated") {
      requestId.current += 1;
      lastEmail.current = null;
      busy.current.clear();
      setPending({});
      setErrors({});
      setNotice("");
      setSnapshot({ status: current.status === "guest" ? "guest" : "error" });
      return;
    }
    if (
      lastEmail.current !== null &&
      lastEmail.current !== current.user.email
    ) {
      // Account changes discard the previous customer's private cart UI.
      busy.current.clear();
      setPending({});
      setErrors({});
      setNotice("");
    }
    lastEmail.current = current.user.email;
    const id = ++requestId.current;
    setSnapshot((previous) =>
      previous && previous.status === "ready"
        ? previous
        : { status: "loading" },
    );
    const controller = new AbortController();
    void fetchCart(id, controller.signal);
  }, [fetchCart]);

  const refreshRef = useRef(refresh);

  useEffect(() => {
    refreshRef.current = refresh;
  }, [refresh]);

  useEffect(() => {
    function load() {
      if (document.visibilityState !== "visible") {
        requestId.current += 1;
        setSnapshot(undefined);
        return;
      }
      refreshRef.current();
    }
    load();
    const rerender = () => load();
    function hide() {
      requestId.current += 1;
      setSnapshot(undefined);
    }
    function visibility() {
      if (document.visibilityState === "visible") load();
      else hide();
    }
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") load();
    }, 60000);
    window.addEventListener("pageshow", rerender);
    window.addEventListener("pagehide", hide);
    window.addEventListener("focus", rerender);
    document.addEventListener("visibilitychange", visibility);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("pageshow", rerender);
      window.removeEventListener("pagehide", hide);
      window.removeEventListener("focus", rerender);
      document.removeEventListener("visibilitychange", visibility);
    };
  }, [session]);

  const mutate = useCallback(
    async (
      productId: number,
      run: (signal: AbortSignal) => Promise<boolean>,
    ) => {
      if (busy.current.has(productId)) return false;
      busy.current.add(productId);
      setPending((previous) => ({ ...previous, [productId]: true }));
      setErrors((previous) => {
        if (!(productId in previous)) return previous;
        const next = { ...previous };
        delete next[productId];
        return next;
      });
      setNotice("");
      try {
        return await run(AbortSignal.timeout(10000));
      } finally {
        busy.current.delete(productId);
        setPending((previous) => {
          if (!(productId in previous)) return previous;
          const next = { ...previous };
          delete next[productId];
          return next;
        });
        // The last write to settle re-reads the authoritative cart so the
        // final UI matches the server after concurrent mutations and
        // refreshes, including mutations whose timeout left the outcome
        // uncertain.
        if (busy.current.size === 0) await reconcile();
      }
    },
    [reconcile],
  );

  const setQuantity = useCallback(
    async (productId: number, quantity: number) => {
      if (!Number.isInteger(quantity) || quantity < 1 || quantity > 99) {
        setErrors((previous) => ({
          ...previous,
          [productId]: "Quantity must be a whole number from 1 to 99.",
        }));
        return false;
      }
      return mutate(productId, async (signal) => {
        const id = ++requestId.current;
        try {
          const response = await fetch(`/api/cart/items/${productId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ quantity }),
            cache: "no-store",
            signal,
          });
          const body = await response.json().catch(() => null);
          if (response.status === 401) {
            applySnapshot(id, { status: "guest" });
            setErrors((previous) => ({
              ...previous,
              [productId]: "Your session expired. Sign in to continue.",
            }));
            return false;
          }
          if (!response.ok || !body || !("items" in (body as object))) {
            setErrors((previous) => ({
              ...previous,
              [productId]: errorMessage(response.status, body),
            }));
            return false;
          }
          applySnapshot(id, { status: "ready", cart: body as Cart });
          return true;
        } catch {
          // A timeout leaves the outcome uncertain: the write may still have
          // settled server-side. Surface a recoverable error; the mutation
          // epilogue re-reads the authoritative cart once quiet.
          setErrors((previous) => ({
            ...previous,
            [productId]: signal.aborted
              ? "The request timed out. Refresh to confirm your cart."
              : "We couldn't connect. Check your connection and try again.",
          }));
          return false;
        }
      });
    },
    [applySnapshot, mutate],
  );

  const removeItem = useCallback(
    async (productId: number) => {
      return mutate(productId, async (signal) => {
        const id = ++requestId.current;
        try {
          const response = await fetch(`/api/cart/items/${productId}`, {
            method: "DELETE",
            cache: "no-store",
            signal,
          });
          if (response.status === 401) {
            applySnapshot(id, { status: "guest" });
            setErrors((previous) => ({
              ...previous,
              [productId]: "Your session expired. Sign in to continue.",
            }));
            return false;
          }
          if (response.status !== 204) {
            const body = await response.json().catch(() => null);
            setErrors((previous) => ({
              ...previous,
              [productId]: errorMessage(response.status, body),
            }));
            return false;
          }
          // Deletion returns no body; the mutation epilogue re-reads the
          // authoritative cart once all writes settle.
          return true;
        } catch {
          // A timeout leaves the outcome uncertain: the removal may still
          // have settled server-side. Surface a recoverable error; the
          // mutation epilogue re-reads the authoritative cart once quiet.
          setErrors((previous) => ({
            ...previous,
            [productId]: signal.aborted
              ? "The request timed out. Refresh to confirm your cart."
              : "We couldn't connect. Check your connection and try again.",
          }));
          return false;
        }
      });
    },
    [applySnapshot, mutate],
  );

  const addItem = useCallback(
    async (productId: number) => {
      const current =
        snapshot && snapshot.status === "ready" ? snapshot.cart : null;
      const existing =
        current?.items.find((item) => item.product.id === productId)
          ?.quantity ?? 0;
      const nextQuantity = existing + 1;
      if (nextQuantity > 99) {
        setErrors((previous) => ({
          ...previous,
          [productId]: "You can keep up to 99 of each object in your cart.",
        }));
        return false;
      }
      const ok = await setQuantity(productId, nextQuantity);
      if (ok) setNotice("Saved to your cart.");
      return ok;
    },
    [setQuantity, snapshot],
  );

  const clearError = useCallback((productId: number) => {
    setErrors((previous) => {
      if (!(productId in previous)) return previous;
      const next = { ...previous };
      delete next[productId];
      return next;
    });
  }, []);

  const value = useMemo<CartContextValue>(() => {
    const state = snapshot ?? { status: "loading" as const };
    return {
      state,
      count: state.status === "ready" ? cartCount(state.cart) : 0,
      pending,
      errors,
      notice,
      refresh,
      setQuantity,
      removeItem,
      addItem,
      clearError,
    };
  }, [
    snapshot,
    pending,
    errors,
    notice,
    refresh,
    setQuantity,
    removeItem,
    addItem,
    clearError,
  ]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}
