import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { NextRequest } from "next/server";
import { getCart, removeItem, setQuantity } from "../src/lib/cart";
import { cartQuantitySchema } from "../src/lib/cart-validation";

const token = "private-cart-token";
const cartBody = {
  currency: "GBP",
  items: [
    {
      available: true,
      line_total: "79.00",
      product: {
        id: 1,
        name: "Oak Monitor Stand",
        description: "Stand",
        price: "79.00",
        currency: "GBP",
        stock: 3,
      },
      quantity: 1,
    },
  ],
  subtotal: "79.00",
};

function mutationRequest(
  body: unknown = { quantity: 2 },
  origin: string | null = "https://shop.test",
) {
  return new NextRequest("https://shop.test/api/cart/items/1", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...(origin ? { Origin: origin } : {}),
      cookie: `__Host-session=${token}`,
    },
    body: JSON.stringify(body),
  });
}

function deleteRequest(origin: string | null = "https://shop.test") {
  return new NextRequest("https://shop.test/api/cart/items/1", {
    method: "DELETE",
    headers: {
      ...(origin ? { Origin: origin } : {}),
      cookie: `__Host-session=${token}`,
    },
  });
}

function getRequest(withToken = true) {
  return new NextRequest("https://shop.test/api/cart", {
    headers: withToken ? { cookie: `__Host-session=${token}` } : {},
  });
}

function upstream(body: unknown, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(status === 204 ? null : JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
}

function params(productId: string) {
  return { params: Promise.resolve({ productId }) };
}

beforeEach(() => {
  vi.stubEnv("APP_ORIGIN", "https://shop.test");
  vi.stubEnv("APP_ORIGIN_ALIASES", "");
  upstream(cartBody);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("cart read boundary", () => {
  it("requires a session without contacting FastAPI", async () => {
    expect((await getCart(getRequest(false))).status).toBe(401);
    expect(fetch).not.toHaveBeenCalled();
  });

  it("returns the backend cart without leaking the bearer", async () => {
    const res = await getCart(getRequest());
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual(cartBody);
    expect(JSON.stringify(await res.json().catch(() => null))).not.toContain(
      token,
    );
    expect(res.headers.get("cache-control")).toContain("no-store");
    expect(res.headers.get("vary")).toContain("Cookie");
    const call = vi.mocked(fetch).mock.calls[0][0] as Request;
    expect(call.headers.get("authorization")).toBe(`Bearer ${token}`);
  });

  it("clears expired sessions but preserves the cookie on outages", async () => {
    upstream({ detail: "invalid" }, 401);
    const expired = await getCart(getRequest());
    expect(expired.status).toBe(401);
    expect(expired.cookies.get("__Host-session")?.maxAge).toBe(0);
    upstream({ detail: "down" }, 500);
    const failed = await getCart(getRequest());
    expect(failed.status).toBe(503);
    expect(failed.headers.get("set-cookie")).toBeNull();
  });
});

describe("cart quantity writes", () => {
  it("rejects missing or mismatched origins before upstream access", async () => {
    for (const origin of [null, "https://evil.test", "null"]) {
      expect(
        (await setQuantity(mutationRequest(undefined, origin), params("1")))
          .status,
      ).toBe(403);
      expect(
        (await removeItem(deleteRequest(origin), params("1"))).status,
      ).toBe(403);
    }
    expect(fetch).not.toHaveBeenCalled();
  });

  it("validates product identifiers before upstream access", async () => {
    for (const productId of ["0", "-1", "abc", "1.5", "9999999999", ""]) {
      expect(
        (await setQuantity(mutationRequest(), params(productId))).status,
      ).toBe(422);
      expect(
        (await removeItem(deleteRequest(), params(productId))).status,
      ).toBe(422);
    }
    expect(fetch).not.toHaveBeenCalled();
  });

  it("validates quantities strictly and rejects extra fields", async () => {
    for (const body of [
      null,
      {},
      { quantity: 0 },
      { quantity: 100 },
      { quantity: 1.5 },
      { quantity: "2" },
      { quantity: 2, price: "1.00" },
      { quantity: 2, product_id: 1 },
      [],
    ]) {
      expect(
        (await setQuantity(mutationRequest(body), params("1"))).status,
      ).toBe(body === null ? 422 : 422);
    }
    expect(fetch).not.toHaveBeenCalled();
  });

  it("rejects non-JSON and malformed quantity payloads", async () => {
    const wrongType = new NextRequest("https://shop.test/api/cart/items/1", {
      method: "PUT",
      headers: {
        Origin: "https://shop.test",
        "Content-Type": "text/plain",
        cookie: `__Host-session=${token}`,
      },
      body: "{}",
    });
    expect((await setQuantity(wrongType, params("1"))).status).toBe(415);
    const malformed = new NextRequest("https://shop.test/api/cart/items/1", {
      method: "PUT",
      headers: {
        Origin: "https://shop.test",
        "Content-Type": "application/json",
        cookie: `__Host-session=${token}`,
      },
      body: "{",
    });
    expect((await setQuantity(malformed, params("1"))).status).toBe(400);
    expect(fetch).not.toHaveBeenCalled();
  });

  it("forwards the bearer and absolute quantity server-side", async () => {
    const res = await setQuantity(
      mutationRequest({ quantity: 2 }),
      params("7"),
    );
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual(cartBody);
    expect(res.headers.get("cache-control")).toContain("no-store");
    const call = vi.mocked(fetch).mock.calls[0][0] as Request;
    expect(call.method).toBe("PUT");
    expect(call.url).toContain("/api/v1/cart/items/7");
    expect(call.headers.get("authorization")).toBe(`Bearer ${token}`);
    expect(await call.json()).toEqual({ quantity: 2 });
  });

  it("maps backend cart outcomes without exposing internals", async () => {
    upstream({ detail: "invalid" }, 401);
    const expired = await setQuantity(mutationRequest(), params("1"));
    expect(expired.status).toBe(401);
    expect(expired.cookies.get("__Host-session")?.maxAge).toBe(0);

    upstream({ detail: "gone" }, 404);
    expect((await setQuantity(mutationRequest(), params("1"))).status).toBe(
      404,
    );

    upstream({ detail: "Only 1 left in stock." }, 409);
    const shortage = await setQuantity(mutationRequest(), params("1"));
    expect(shortage.status).toBe(409);
    expect(await shortage.json()).toEqual({
      error: "Only 1 left in stock.",
    });

    upstream({ detail: "validation" }, 422);
    expect((await setQuantity(mutationRequest(), params("1"))).status).toBe(
      422,
    );

    upstream({ detail: "private" }, 500);
    const failed = await setQuantity(mutationRequest(), params("1"));
    expect(failed.status).toBe(503);
    expect(JSON.stringify(await failed.json())).not.toContain("private");
  });

  it("requires a session for writes", async () => {
    const guest = new NextRequest("https://shop.test/api/cart/items/1", {
      method: "PUT",
      headers: {
        Origin: "https://shop.test",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ quantity: 1 }),
    });
    expect((await setQuantity(guest, params("1"))).status).toBe(401);
    expect(fetch).not.toHaveBeenCalled();
  });
});

describe("cart removal", () => {
  it("returns private no-store 204 for removed and missing lines", async () => {
    upstream(null, 204);
    const removed = await removeItem(deleteRequest(), params("3"));
    expect(removed.status).toBe(204);
    expect(removed.headers.get("cache-control")).toContain("no-store");
    const call = vi.mocked(fetch).mock.calls[0][0] as Request;
    expect(call.method).toBe("DELETE");
    expect(call.url).toContain("/api/v1/cart/items/3");
    expect(call.headers.get("authorization")).toBe(`Bearer ${token}`);
  });

  it("clears expired sessions and maps failures", async () => {
    upstream({ detail: "invalid" }, 401);
    const expired = await removeItem(deleteRequest(), params("1"));
    expect(expired.status).toBe(401);
    expect(expired.cookies.get("__Host-session")?.maxAge).toBe(0);
    upstream({ detail: "down" }, 500);
    const failed = await removeItem(deleteRequest(), params("1"));
    expect(failed.status).toBe(503);
    expect(failed.headers.get("set-cookie")).toBeNull();
  });

  it("requires a session for removal", async () => {
    const guest = new NextRequest("https://shop.test/api/cart/items/1", {
      method: "DELETE",
      headers: { Origin: "https://shop.test" },
    });
    expect((await removeItem(guest, params("1"))).status).toBe(401);
    expect(fetch).not.toHaveBeenCalled();
  });
});

describe("cart configuration boundary", () => {
  it("fails closed for absent or non-canonical origins", async () => {
    for (const origin of ["", "https://shop.test/", "invalid"]) {
      vi.stubEnv("APP_ORIGIN", origin);
      expect((await getCart(getRequest())).status).toBe(503);
      expect((await setQuantity(mutationRequest(), params("1"))).status).toBe(
        503,
      );
      expect((await removeItem(deleteRequest(), params("1"))).status).toBe(503);
    }
    expect(fetch).not.toHaveBeenCalled();
  });
});

describe("cart quantity schema", () => {
  it("accepts whole quantities from 1 to 99", () => {
    expect(cartQuantitySchema.safeParse({ quantity: 1 }).success).toBe(true);
    expect(cartQuantitySchema.safeParse({ quantity: 99 }).success).toBe(true);
  });

  it("rejects invalid, missing and extra quantity input", () => {
    for (const input of [
      { quantity: 0 },
      { quantity: 100 },
      { quantity: 1.5 },
      { quantity: "2" },
      {},
    ]) {
      expect(cartQuantitySchema.safeParse(input).success).toBe(false);
    }
  });
});
