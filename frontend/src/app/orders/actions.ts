"use server";

import { headers } from "next/headers";
import { revalidatePath } from "next/cache";
import { apiClient } from "@/lib/api/client";
import { cartIdentity, CartRateLimitError } from "@/lib/cart-data";
import { sessionPolicy } from "@/lib/session";
import { rateLimitMessage, retryAfterSeconds } from "@/lib/rate-limit";

export type CheckoutResult = { error: string; location?: string };

export async function prepareCheckout(
  owner: string,
  _previous: CheckoutResult,
  _form: FormData,
): Promise<CheckoutResult> {
  void _previous;
  void _form;
  let id: number;
  try {
    if (
      !sessionPolicy().origins.includes((await headers()).get("origin") ?? "")
    )
      return { error: "Origin rejected." };
    const identity = await cartIdentity();
    if (!identity || identity.owner !== owner)
      return {
        error: "Your session changed. Sign in and review your cart again.",
      };
    const client = apiClient();
    const auth = { Authorization: `Bearer ${identity.token}` };
    const cart = await client.GET("/api/v1/cart/", {
      headers: auth,
      redirect: "error",
    });
    if (cart.response.status === 429)
      return {
        error: rateLimitMessage(
          retryAfterSeconds(cart.response.headers.get("Retry-After")),
        ),
      };
    if (cart.response.status === 401)
      return {
        error: "Your session expired. Sign in and review your cart again.",
      };
    if (cart.response.status !== 200 || !cart.data?.items.length)
      return {
        error:
          "Your cart is empty or unavailable. Refresh it before continuing.",
      };
    if (cart.data.items.some((item) => !item.available)) {
      revalidatePath("/cart");
      return {
        error:
          "Some items are no longer available in that quantity. Update your cart before checkout.",
      };
    }
    const draft = await client.POST("/api/v1/orders/drafts", {
      headers: auth,
      redirect: "error",
      body: {
        lines: cart.data.items.map((item) => ({
          product_id: item.product.id,
          quantity: item.quantity,
        })),
      },
    });
    if (draft.response.status === 429)
      return {
        error: rateLimitMessage(
          retryAfterSeconds(draft.response.headers.get("Retry-After")),
        ),
      };
    if (!draft.data || draft.response.status !== 201)
      return {
        error:
          "We couldn't prepare your order. Review your cart and try again.",
      };
    id = draft.data.id;
  } catch (error) {
    if (error instanceof CartRateLimitError)
      return { error: rateLimitMessage(error.retryAfterSeconds) };
    return {
      error:
        "We couldn't confirm your draft. Check order history before trying again. No payment has been taken.",
    };
  }
  return { error: "", location: `/orders/${id}` };
}

export async function placeCheckout(
  owner: string,
  id: number,
  _previous: CheckoutResult,
  _form: FormData,
): Promise<CheckoutResult> {
  void _previous;
  void _form;
  try {
    if (!Number.isSafeInteger(id) || id < 1 || id > 2147483647)
      return { error: "Invalid order." };
    if (
      !sessionPolicy().origins.includes((await headers()).get("origin") ?? "")
    )
      return { error: "Origin rejected." };
    const identity = await cartIdentity();
    if (!identity || identity.owner !== owner)
      return {
        error:
          "Your session changed. Sign in to the original account to continue.",
      };
    const result = await apiClient().POST("/api/v1/orders/{order_id}/place", {
      redirect: "error",
      params: {
        path: { order_id: id },
        // Stable across reloads and response loss; scoped to the customer by FastAPI.
        header: { "idempotency-key": `storefront-order-${id}` },
      },
      headers: {
        Authorization: `Bearer ${identity.token}`,
      },
    });
    if (result.response.status === 429)
      return {
        error: rateLimitMessage(
          retryAfterSeconds(result.response.headers.get("Retry-After")),
        ),
      };
    if (result.response.status === 409) {
      revalidatePath("/cart");
      return {
        error:
          "Your cart, price or stock changed. Return to your cart and prepare a new order to review.",
      };
    }
    if (result.response.status === 401 || result.response.status === 404)
      return { error: "This order is unavailable for your current session." };
    if (!result.data || result.response.status !== 200)
      return {
        error:
          "We couldn't confirm placement. Retry this same order; it will not be placed twice.",
      };
  } catch (error) {
    if (error instanceof CartRateLimitError)
      return { error: rateLimitMessage(error.retryAfterSeconds) };
    return {
      error:
        "We couldn't confirm placement. Retry this same order; it will not be placed twice.",
    };
  }
  revalidatePath("/cart");
  revalidatePath("/orders");
  return { error: "", location: `/orders/${id}` };
}
