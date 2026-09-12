"use server";

import { refresh } from "next/cache";
import { headers } from "next/headers";
import { z } from "zod";
import { apiClient } from "@/lib/api/client";
import { cartIdentity } from "@/lib/cart-data";
import { sessionPolicy } from "@/lib/session";
import type { CartActionResult, CartChange } from "@/lib/cart-state";

const productId = z.number().int().min(1).max(2147483647);
const changeSchema = z.discriminatedUnion("kind", [
  z
    .object({
      kind: z.literal("set"),
      productId,
      quantity: z.number().int().min(1).max(99),
    })
    .strict(),
  z.object({ kind: z.literal("add"), productId }).strict(),
  z.object({ kind: z.literal("remove"), productId }).strict(),
]);

export async function changeCart(
  expectedOwner: string,
  input: CartChange,
): Promise<CartActionResult> {
  let result: CartActionResult;
  try {
    // Retain the deployment's explicit origin allowlist as well as Next's CSRF check.
    if (
      !sessionPolicy().origins.includes((await headers()).get("origin") ?? "")
    )
      return { ok: false, error: "Origin rejected." };
    const parsed = changeSchema.safeParse(input);
    if (!parsed.success)
      return {
        ok: false,
        error: "Quantity must be a whole number from 1 to 99.",
      };
    const identity = await cartIdentity();
    if (!identity || identity.owner !== expectedOwner) {
      result = {
        ok: false,
        error: "Your session changed. Refresh your cart before trying again.",
      };
    } else {
      const change = parsed.data;
      const options = {
        redirect: "error" as const,
        params: { path: { product_id: change.productId } },
        headers: { Authorization: `Bearer ${identity.token}` },
      };
      const client = apiClient();
      let quantity = change.kind === "set" ? change.quantity : 1;
      if (change.kind === "add") {
        const current = await client.GET("/api/v1/cart/", {
          redirect: options.redirect,
          headers: options.headers,
        });
        if (current.response.status !== 200 || !current.data)
          throw new Error("Cart unavailable");
        quantity +=
          current.data.items.find(
            (item) => item.product.id === change.productId,
          )?.quantity ?? 0;
      }
      if (quantity > 99) {
        refresh();
        return {
          ok: false,
          error: "You can keep up to 99 of each object in your cart.",
        };
      }
      const response =
        change.kind === "remove"
          ? await client.DELETE("/api/v1/cart/items/{product_id}", options)
          : await client.PUT("/api/v1/cart/items/{product_id}", {
              ...options,
              body: { quantity },
            });
      const status = response.response.status;
      if (
        status === 200 ||
        status === 204 ||
        (change.kind === "remove" && status === 404)
      ) {
        result = { ok: true };
      } else {
        const error =
          status === 409
            ? "Not enough stock for that quantity. Stock is not reserved."
            : status === 401
              ? "Your session expired. Sign in to continue."
              : status === 404
                ? "This product is no longer available."
                : status === 422
                  ? "Quantity must be a whole number from 1 to 99."
                  : "Your cart is temporarily unavailable. Please try again.";
        result = { ok: false, error };
      }
    }
  } catch {
    result = {
      ok: false,
      error:
        "We couldn't confirm the change. Refresh your cart before trying again.",
      uncertain: true,
    };
  }
  // Reads are private/no-store. Next includes the refreshed server tree with
  // this action response, including after a write with an uncertain outcome.
  refresh();
  return result;
}
