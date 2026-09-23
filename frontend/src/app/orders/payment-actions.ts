"use server";

import { headers } from "next/headers";
import { revalidatePath } from "next/cache";
import { apiClient } from "@/lib/api/client";
import { cartIdentity, CartRateLimitError } from "@/lib/cart-data";
import { sessionPolicy } from "@/lib/session";
import { rateLimitMessage, retryAfterSeconds } from "@/lib/rate-limit";
import type { CheckoutResult } from "./actions";

type PaymentOperation = "payment" | "cancel" | "reconcile";

async function mutatePayment(
  operation: PaymentOperation,
  owner: string,
  id: number,
): Promise<CheckoutResult> {
  const uncertain = {
    error:
      "We couldn't confirm the payment status. Check this order's status before trying again. Do not start another order.",
  };
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
    const options = {
      redirect: "error" as const,
      params: { path: { order_id: id } },
      headers: { Authorization: `Bearer ${identity.token}` },
    };
    const client = apiClient();
    const result =
      operation === "payment"
        ? await client.POST("/api/v1/orders/{order_id}/payment", options)
        : operation === "cancel"
          ? await client.POST("/api/v1/orders/{order_id}/cancel", options)
          : await client.POST("/api/v1/orders/{order_id}/reconcile", options);
    if (result.response.status === 429)
      return {
        error: rateLimitMessage(
          retryAfterSeconds(result.response.headers.get("Retry-After")),
        ),
      };
    if (result.response.status === 401 || result.response.status === 404)
      return { error: "This order is unavailable for your current session." };
    if (result.response.status === 409) {
      revalidatePath(`/orders/${id}`);
      return {
        error:
          "This order's payment state changed. Refresh the order before continuing.",
      };
    }
    if (result.response.status !== 200 || !result.data) return uncertain;
    if (
      operation === "cancel" &&
      "payment_status" in result.data &&
      result.data.payment_status === "pending"
    )
      return {
        error:
          "This payment is still processing and could not be cancelled. Stock remains reserved. Check payment status before trying again.",
      };
    revalidatePath("/orders");
    revalidatePath(`/orders/${id}`);
    if (
      operation === "payment" &&
      "checkout_url" in result.data &&
      result.data.checkout_url
    ) {
      const url = new URL(result.data.checkout_url);
      if (
        url.protocol !== "https:" ||
        url.hostname !== "checkout.stripe.com" ||
        url.port ||
        url.username ||
        url.password
      )
        return uncertain;
      return { error: "", location: url.href };
    }
    return { error: "", location: `/orders/${id}` };
  } catch (error) {
    if (error instanceof CartRateLimitError)
      return { error: rateLimitMessage(error.retryAfterSeconds) };
    return uncertain;
  }
}

export async function startPayment(
  owner: string,
  id: number,
  _previous: CheckoutResult,
  _form: FormData,
): Promise<CheckoutResult> {
  void _previous;
  void _form;
  return mutatePayment("payment", owner, id);
}

export async function cancelPayment(
  owner: string,
  id: number,
  _previous: CheckoutResult,
  _form: FormData,
): Promise<CheckoutResult> {
  void _previous;
  void _form;
  return mutatePayment("cancel", owner, id);
}

export async function reconcilePayment(
  owner: string,
  id: number,
  _previous: CheckoutResult,
  _form: FormData,
): Promise<CheckoutResult> {
  void _previous;
  void _form;
  return mutatePayment("reconcile", owner, id);
}
