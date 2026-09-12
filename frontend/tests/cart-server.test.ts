import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
const runtime = vi.hoisted(() => ({
  token: "private-token",
  origin: "https://shop.test",
  refresh: vi.fn(),
}));
vi.mock("next/headers", () => ({
  cookies: async () => ({
    get: () => (runtime.token ? { value: runtime.token } : undefined),
  }),
  headers: async () =>
    new Headers(runtime.origin ? { origin: runtime.origin } : {}),
}));
vi.mock("next/cache", () => ({ refresh: runtime.refresh }));
import { readCartSnapshot } from "../src/lib/cart-data";
import { changeCart } from "../src/app/cart/actions";
import type { CartChange } from "../src/lib/cart-state";
const owner = "customer@example.test";
const cart = {
  currency: "GBP",
  items: [{ product: { id: 1 }, quantity: 2 }],
  subtotal: "10.00",
};
function upstream({
  identity = 200,
  read = 200,
  write = 200,
  fail = false,
  quantity = 2,
} = {}) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (request: Request) => {
      if (fail) throw new Error("private infrastructure failure");
      const path = new URL(request.url).pathname;
      const status = path.endsWith("/auth/me")
        ? identity
        : request.method === "GET"
          ? read
          : write;
      const body = path.endsWith("/auth/me")
        ? { email: owner }
        : { ...cart, items: [{ product: { id: 1 }, quantity }] };
      return new Response(status === 204 ? null : JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      });
    }),
  );
}
beforeEach(() => {
  vi.stubEnv("APP_ORIGIN", "https://shop.test");
  vi.stubEnv("APP_ORIGIN_ALIASES", "");
  runtime.token = "private-token";
  runtime.origin = "https://shop.test";
  runtime.refresh.mockReset();
  upstream();
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("server-rendered cart", () => {
  it("does not contact FastAPI for a guest", async () => {
    runtime.token = "";
    expect(await readCartSnapshot()).toEqual({ status: "guest", owner: null });
    expect(fetch).not.toHaveBeenCalled();
  });
  it("returns only verified identity and cart, never the bearer", async () => {
    const result = await readCartSnapshot();
    expect(result).toEqual({ status: "ready", owner, cart });
    expect(JSON.stringify(result)).not.toContain(runtime.token);
    for (const [request] of vi.mocked(fetch).mock.calls) {
      expect((request as Request).headers.get("authorization")).toBe(
        `Bearer ${runtime.token}`,
      );
      expect((request as Request).cache).toBe("no-store");
    }
  });
  it.each([401, 503])(
    "handles identity status %s without returning a previous owner",
    async (identity) => {
      upstream({ identity });
      expect(await readCartSnapshot()).toEqual({
        status: identity === 401 ? "guest" : "error",
        owner: null,
      });
    },
  );
  it.each([401, 503])("handles cart status %s", async (read) => {
    upstream({ read });
    expect(await readCartSnapshot()).toEqual({
      status: read === 401 ? "guest" : "error",
      owner: read === 401 ? null : owner,
    });
  });
  it("sanitizes transport failures", async () => {
    upstream({ fail: true });
    expect(await readCartSnapshot()).toEqual({ status: "error", owner: null });
  });
});

describe("cart Server Action", () => {
  it.each(["", "https://evil.test"])(
    "rejects origin %s before backend calls",
    async (origin) => {
      runtime.origin = origin;
      expect(
        await changeCart(owner, { kind: "add", productId: 1 }),
      ).toMatchObject({ ok: false, error: "Origin rejected." });
      expect(fetch).not.toHaveBeenCalled();
    },
  );
  it.each([
    { kind: "set", productId: 1, quantity: 0 },
    { kind: "set", productId: 1, quantity: 100 },
    { kind: "set", productId: 1, quantity: 1.5 },
    { kind: "remove", productId: -1 },
    { kind: "add", productId: 1, owner: "someone" },
  ])("validates untrusted input %j", async (input) => {
    expect(await changeCart(owner, input as CartChange)).toMatchObject({
      ok: false,
    });
    expect(fetch).not.toHaveBeenCalled();
  });
  it("rejects a stale page's owner even with a valid new-account cookie", async () => {
    expect(
      await changeCart("previous@example.test", {
        kind: "set",
        productId: 1,
        quantity: 3,
      }),
    ).toMatchObject({
      ok: false,
      error: expect.stringContaining("session changed"),
    });
    expect(vi.mocked(fetch).mock.calls).toHaveLength(1);
    expect(runtime.refresh).toHaveBeenCalledOnce();
  });
  it("requires a valid session for every mutation", async () => {
    runtime.token = "";
    expect(
      await changeCart(owner, { kind: "remove", productId: 1 }),
    ).toMatchObject({ ok: false });
    expect(fetch).not.toHaveBeenCalled();
  });
  it("adds using the current server quantity", async () => {
    expect(await changeCart(owner, { kind: "add", productId: 1 })).toEqual({
      ok: true,
    });
    const request = vi.mocked(fetch).mock.calls.at(-1)![0] as Request;
    expect(await request.json()).toEqual({ quantity: 3 });
    expect(runtime.refresh).toHaveBeenCalledOnce();
  });
  it("adds a new line with quantity one", async () => {
    expect(await changeCart(owner, { kind: "add", productId: 2 })).toEqual({
      ok: true,
    });
    expect(
      await (vi.mocked(fetch).mock.calls.at(-1)![0] as Request).json(),
    ).toEqual({ quantity: 1 });
  });
  it("does not increment beyond the quantity limit", async () => {
    upstream({ quantity: 99 });
    expect(
      await changeCart(owner, { kind: "add", productId: 1 }),
    ).toMatchObject({ ok: false, error: expect.stringContaining("99") });
    expect(vi.mocked(fetch).mock.calls).toHaveLength(2);
  });
  it("does not write when the pre-add read fails", async () => {
    upstream({ read: 503 });
    expect(
      await changeCart(owner, { kind: "add", productId: 1 }),
    ).toMatchObject({ ok: false });
    expect(vi.mocked(fetch).mock.calls).toHaveLength(2);
    expect(runtime.refresh).toHaveBeenCalledOnce();
  });
  it.each([204, 404])("removal accepts idempotent status %s", async (write) => {
    upstream({ write });
    expect(await changeCart(owner, { kind: "remove", productId: 1 })).toEqual({
      ok: true,
    });
    expect((vi.mocked(fetch).mock.calls.at(-1)![0] as Request).method).toBe(
      "DELETE",
    );
  });
  it.each([
    [401, "session expired"],
    [404, "no longer available"],
    [409, "Not enough stock"],
    [422, "whole number"],
    [503, "temporarily unavailable"],
  ] as const)("maps status %s safely and refreshes", async (write, message) => {
    upstream({ write });
    expect(
      await changeCart(owner, { kind: "set", productId: 1, quantity: 3 }),
    ).toMatchObject({ ok: false, error: expect.stringContaining(message) });
    expect(runtime.refresh).toHaveBeenCalledOnce();
  });
  it("refreshes after transport failure without claiming the write was undone", async () => {
    upstream({ fail: true });
    expect(await changeCart(owner, { kind: "add", productId: 1 })).toEqual({
      ok: false,
      error:
        "We couldn't confirm the change. Refresh your cart before trying again.",
    });
    expect(runtime.refresh).toHaveBeenCalledOnce();
  });
});
