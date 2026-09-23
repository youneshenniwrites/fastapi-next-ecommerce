import { beforeEach, expect, it, vi } from "vitest";
const { identity, post, refresh, origin } = vi.hoisted(() => ({
  identity: vi.fn(),
  post: vi.fn(),
  refresh: vi.fn(),
  origin: vi.fn(),
}));
vi.mock("next/headers", () => ({ headers: async () => ({ get: origin }) }));
vi.mock("next/cache", () => ({ revalidatePath: refresh }));
vi.mock("server-only", () => ({}));
vi.mock("@/lib/cart-data", async (original) => ({
  ...(await original<typeof import("@/lib/cart-data")>()),
  cartIdentity: identity,
}));
vi.mock("@/lib/session", () => ({
  sessionPolicy: () => ({ origins: ["https://shop.example"] }),
}));
vi.mock("@/lib/api/client", () => ({ apiClient: () => ({ POST: post }) }));
import {
  startPayment,
  cancelPayment,
  reconcilePayment,
} from "../src/app/orders/payment-actions";
import { CartRateLimitError } from "@/lib/cart-data";
const reply = (status: number, data?: unknown) => ({
  response: new Response(null, { status, headers: { "Retry-After": "12" } }),
  data,
});
beforeEach(() => {
  vi.resetAllMocks();
  origin.mockReturnValue("https://shop.example");
  identity.mockResolvedValue({
    owner: "a@example.com",
    token: "fictional-token",
  });
  post.mockResolvedValue(reply(200, { id: 7 }));
});
for (const action of [startPayment, cancelPayment, reconcilePayment]) {
  const run = (id = 7) =>
    action("a@example.com", id, { error: "" }, new FormData());
  it(`${action.name}: rejects an untrusted origin before identity`, async () => {
    origin.mockReturnValue("https://evil.example");
    expect((await run()).error).toMatch(/Origin/);
    expect(identity).not.toHaveBeenCalled();
    expect(post).not.toHaveBeenCalled();
  });
  it(`${action.name}: prevents account switching`, async () => {
    identity.mockResolvedValue({ owner: "b@example.com", token: "other" });
    expect((await run()).error).toMatch(/session changed/);
    expect(post).not.toHaveBeenCalled();
  });
  it(`${action.name}: validates the order ID`, async () => {
    for (const id of [0, -1, NaN, 1.5, 2147483648])
      expect((await run(id)).error).toBe("Invalid order.");
    expect(post).not.toHaveBeenCalled();
  });
  it(`${action.name}: preserves throttling before and during the mutation`, async () => {
    identity.mockRejectedValueOnce(new CartRateLimitError(12));
    expect((await run()).error).toContain("12 seconds");
    expect(post).not.toHaveBeenCalled();
    post.mockResolvedValue(reply(429));
    expect((await run()).error).toContain("12 seconds");
    expect(post).toHaveBeenCalledTimes(1);
  });
  it(`${action.name}: never automatically repeats an uncertain write`, async () => {
    post.mockRejectedValue(new Error("private provider details"));
    expect((await run()).error).toMatch(/Check this order's status/);
    expect(post).toHaveBeenCalledTimes(1);
    expect(refresh).not.toHaveBeenCalled();
  });
  it(`${action.name}: returns to the owned order without claiming payment`, async () => {
    expect(await run()).toEqual({ error: "", location: "/orders/7" });
    expect(post.mock.calls[0][1]).toMatchObject({
      redirect: "error",
      params: { path: { order_id: 7 } },
      headers: { Authorization: "Bearer fictional-token" },
    });
  });
  for (const status of [401, 404, 409, 503])
    it(`${action.name}: handles ${status}`, async () => {
      post.mockResolvedValue(reply(status));
      expect((await run()).error).toBeTruthy();
      expect(post).toHaveBeenCalledTimes(1);
    });
}
for (const url of [
  "https://evil.example",
  "http://checkout.stripe.com/pay",
  "https://checkout.stripe.com.evil.example",
  "https://attacker@checkout.stripe.com/pay",
  "javascript:alert(1)",
  "https://checkout.stripe.com:8443/pay",
  "/relative",
]) {
  it(`rejects unsafe payment destination ${url}`, async () => {
    post.mockResolvedValue(reply(200, { checkout_url: url }));
    const result = await startPayment(
      "a@example.com",
      7,
      { error: "" },
      new FormData(),
    );
    expect(result.location).toBeUndefined();
    expect(result.error).toBeTruthy();
  });
}
it("accepts only the hosted Stripe checkout destination", async () => {
  post.mockResolvedValue(
    reply(200, {
      checkout_url: "https://checkout.stripe.com/c/pay/cs_test_fictional",
    }),
  );
  expect(
    await startPayment("a@example.com", 7, { error: "" }, new FormData()),
  ).toEqual({
    error: "",
    location: "https://checkout.stripe.com/c/pay/cs_test_fictional",
  });
});

it("explains why a processing payment could not be cancelled", async () => {
  post.mockResolvedValue(reply(200, { payment_status: "pending" }));
  const result = await cancelPayment(
    "a@example.com",
    7,
    { error: "" },
    new FormData(),
  );
  expect(result.error).toContain("could not be cancelled");
  expect(result.location).toBeUndefined();
});
