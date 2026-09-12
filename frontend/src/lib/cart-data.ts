import "server-only";
import { cache } from "react";
import { cookies } from "next/headers";
import { apiClient } from "./api/client";
import { sessionPolicy } from "./session";
import type { CartSnapshot } from "./cart-state";

// Resolve identity through FastAPI. Neither client props nor decoded JWT claims
// establish ownership. This result (including the token) stays server-only.
export async function cartIdentity() {
  const token = (await cookies()).get(sessionPolicy().name)?.value;
  if (!token) return null;
  const result = await apiClient().GET("/api/v1/auth/me", {
    redirect: "error",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (result.response.status === 401) return null;
  if (result.response.status !== 200 || !result.data)
    throw new Error("Session unavailable");
  return { token, owner: result.data.email };
}

// Share one private result across the layout and page in this server render.
// React cache is request-scoped: no data is reused across requests or users.
export const readCartSnapshot = cache(async (): Promise<CartSnapshot> => {
  let owner: string | null = null;
  try {
    const identity = await cartIdentity();
    if (!identity) return { status: "guest", owner: null };
    owner = identity.owner;
    const result = await apiClient().GET("/api/v1/cart/", {
      redirect: "error",
      headers: { Authorization: `Bearer ${identity.token}` },
    });
    if (result.response.status === 401) return { status: "guest", owner: null };
    if (result.response.status !== 200 || !result.data)
      return { status: "error", owner };
    return { status: "ready", owner, cart: result.data };
  } catch {
    return { status: "error", owner };
  }
});
