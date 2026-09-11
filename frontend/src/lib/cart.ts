import "server-only";
import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "./api/client";

function policy() {
  const raw = process.env.APP_ORIGIN;
  if (!raw) throw new Error("APP_ORIGIN is required for sessions");
  const origin = new URL(raw);
  if (origin.origin !== raw || origin.username || origin.password)
    throw new Error("APP_ORIGIN must be an origin");
  const secure = origin.protocol === "https:";
  if (
    !secure &&
    !(
      origin.protocol === "http:" &&
      ["localhost", "127.0.0.1", "[::1]"].includes(origin.hostname) &&
      process.env.ALLOW_LOCAL_HTTP_SESSIONS === "true"
    )
  )
    throw new Error(
      "Sessions require HTTPS or explicit loopback development mode",
    );
  const aliases: unknown = JSON.parse(process.env.APP_ORIGIN_ALIASES || "[]");
  if (!Array.isArray(aliases) || aliases.length > 5)
    throw new Error(
      "APP_ORIGIN_ALIASES must be an array of at most five origins",
    );
  for (const alias of aliases) {
    if (typeof alias !== "string") throw new Error("Invalid origin alias");
    const parsed = new URL(alias);
    if (!secure || parsed.protocol !== "https:" || parsed.origin !== alias)
      throw new Error("Origin aliases must be exact HTTPS origins");
  }
  return {
    origins: [raw, ...aliases],
    secure,
    name: secure ? "__Host-session" : "local-session",
  };
}

function reply(body: object, status = 200) {
  return NextResponse.json(body, {
    status,
    headers: {
      "Cache-Control": "private, no-store",
      Vary: "Cookie",
    },
  });
}

function clear(response: NextResponse, config: ReturnType<typeof policy>) {
  response.cookies.set(config.name, "", {
    httpOnly: true,
    secure: config.secure,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  return response;
}

function noStore(status = 204) {
  return new NextResponse(null, {
    status,
    headers: {
      "Cache-Control": "private, no-store",
      Vary: "Cookie",
    },
  });
}

function productIdFrom(value: unknown) {
  if (typeof value !== "string" || !/^\d+$/.test(value)) return null;
  const id = Number(value);
  if (!Number.isSafeInteger(id) || id < 1 || id > 2147483647) return null;
  return id;
}

function quantityFrom(input: unknown) {
  if (!input || typeof input !== "object" || Array.isArray(input)) return null;
  const keys = Object.keys(input as Record<string, unknown>);
  if (keys.length !== 1 || keys[0] !== "quantity") return null;
  const quantity = (input as { quantity?: unknown }).quantity;
  if (typeof quantity !== "number" || !Number.isInteger(quantity)) return null;
  if (quantity < 1 || quantity > 99) return null;
  return quantity;
}

function backendDetail(data: unknown, fallback: string) {
  if (
    data &&
    typeof data === "object" &&
    typeof (data as { detail?: unknown }).detail === "string"
  ) {
    const detail = (data as { detail: string }).detail.trim();
    if (detail) return detail;
  }
  return fallback;
}

export async function getCart(request: NextRequest) {
  try {
    const config = policy();
    const token = request.cookies.get(config.name)?.value;
    if (!token) return reply({ error: "Sign in required" }, 401);
    const result = await apiClient().GET("/api/v1/cart/", {
      redirect: "error",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (result.response.status === 401)
      return clear(reply({ error: "Sign in required" }, 401), config);
    if (!result.data || result.response.status !== 200)
      return reply({ error: "Your cart is temporarily unavailable." }, 503);
    return reply(result.data);
  } catch {
    return reply({ error: "Your cart is temporarily unavailable." }, 503);
  }
}

export async function setQuantity(
  request: NextRequest,
  context: { params: Promise<{ productId: string }> },
) {
  try {
    const config = policy();
    if (!config.origins.includes(request.headers.get("origin") ?? ""))
      return reply({ error: "Origin rejected" }, 403);
    if (!request.headers.get("content-type")?.startsWith("application/json"))
      return reply({ error: "Expected JSON" }, 415);
    const { productId } = await context.params;
    const id = productIdFrom(productId);
    if (id === null) return reply({ error: "Invalid product." }, 422);
    let input: unknown;
    try {
      input = await request.json();
    } catch {
      return reply({ error: "Invalid quantity." }, 400);
    }
    const quantity = quantityFrom(input);
    if (quantity === null)
      return reply(
        { error: "Quantity must be a whole number from 1 to 99." },
        422,
      );
    const token = request.cookies.get(config.name)?.value;
    if (!token) return reply({ error: "Sign in required" }, 401);
    const result = await apiClient().PUT("/api/v1/cart/items/{product_id}", {
      redirect: "error",
      params: { path: { product_id: id } },
      body: { quantity },
      headers: { Authorization: `Bearer ${token}` },
    });
    if (result.response.status === 401)
      return clear(reply({ error: "Sign in required" }, 401), config);
    if (result.response.status === 404)
      return reply({ error: "This product is no longer available." }, 404);
    if (result.response.status === 409)
      return reply(
        {
          error: backendDetail(
            result.error ?? result.data,
            "Not enough stock for that quantity. Stock is not reserved.",
          ),
        },
        409,
      );
    if (result.response.status === 422)
      return reply(
        { error: "Quantity must be a whole number from 1 to 99." },
        422,
      );
    if (!result.data || result.response.status !== 200)
      return reply({ error: "Your cart is temporarily unavailable." }, 503);
    return reply(result.data);
  } catch {
    return reply({ error: "Your cart is temporarily unavailable." }, 503);
  }
}

export async function removeItem(
  request: NextRequest,
  context: { params: Promise<{ productId: string }> },
) {
  try {
    const config = policy();
    if (!config.origins.includes(request.headers.get("origin") ?? ""))
      return reply({ error: "Origin rejected" }, 403);
    const { productId } = await context.params;
    const id = productIdFrom(productId);
    if (id === null) return reply({ error: "Invalid product." }, 422);
    const token = request.cookies.get(config.name)?.value;
    if (!token) return reply({ error: "Sign in required" }, 401);
    const result = await apiClient().DELETE("/api/v1/cart/items/{product_id}", {
      redirect: "error",
      params: { path: { product_id: id } },
      headers: { Authorization: `Bearer ${token}` },
    });
    if (result.response.status === 401)
      return clear(reply({ error: "Sign in required" }, 401), config);
    if (result.response.status === 204 || result.response.status === 404)
      return noStore(204);
    if (result.response.status === 422)
      return reply({ error: "Invalid product." }, 422);
    return reply({ error: "Your cart is temporarily unavailable." }, 503);
  } catch {
    return reply({ error: "Your cart is temporarily unavailable." }, 503);
  }
}
