import "server-only";

import { cache } from "react";
import type { components } from "@/lib/api/schema";
import { apiClient } from "@/lib/api/client";
import { cartIdentity } from "@/lib/cart-data";

type Order = components["schemas"]["OrderRead"];
type OrderReadResult<T> =
  | { status: "ready"; owner: string; data: T }
  | { status: "guest" | "error" | "missing" };

// Request-scoped only. FastAPI enforces ownership; bearer credentials never
// appear in the value passed to a page or client component.
export const readOrder = cache(
  async (id: number): Promise<OrderReadResult<Order>> => {
    if (!Number.isSafeInteger(id) || id < 1 || id > 2147483647)
      return { status: "missing" };
    try {
      const identity = await cartIdentity();
      if (!identity) return { status: "guest" };
      const result = await apiClient().GET("/api/v1/orders/{order_id}", {
        redirect: "error",
        params: { path: { order_id: id } },
        headers: { Authorization: `Bearer ${identity.token}` },
      });
      if (result.response.status === 401) return { status: "guest" };
      if (result.response.status === 404) return { status: "missing" };
      if (result.response.status !== 200 || !result.data)
        return { status: "error" };
      return { status: "ready", owner: identity.owner, data: result.data };
    } catch {
      return { status: "error" };
    }
  },
);

export const readOrders = cache(
  async (afterId?: number): Promise<OrderReadResult<Order[]>> => {
    try {
      const identity = await cartIdentity();
      if (!identity) return { status: "guest" };
      const result = await apiClient().GET("/api/v1/orders/", {
        redirect: "error",
        params: { query: { limit: 21, after_id: afterId } },
        headers: { Authorization: `Bearer ${identity.token}` },
      });
      if (result.response.status === 401) return { status: "guest" };
      if (result.response.status !== 200 || !result.data)
        return { status: "error" };
      return { status: "ready", owner: identity.owner, data: result.data };
    } catch {
      return { status: "error" };
    }
  },
);
