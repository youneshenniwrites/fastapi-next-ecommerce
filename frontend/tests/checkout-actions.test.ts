import { beforeEach, expect, it, vi } from "vitest";
const { identity, get, post, refresh, origin } = vi.hoisted(() => ({
  identity: vi.fn(),
  get: vi.fn(),
  post: vi.fn(),
  refresh: vi.fn(),
  origin: vi.fn(),
}));
vi.mock("next/headers", () => ({ headers: async () => ({ get: origin }) }));
vi.mock("next/cache", () => ({ revalidatePath: refresh }));
vi.mock("@/lib/cart-data", () => ({ cartIdentity: identity }));
vi.mock("@/lib/session", () => ({
  sessionPolicy: () => ({ origins: ["https://shop.example"] }),
}));
vi.mock("@/lib/api/client", () => ({
  apiClient: () => ({ GET: get, POST: post }),
}));
import { prepareCheckout, placeCheckout } from "../src/app/orders/actions";
const response = (status: number, data?: unknown, retry?: string) => ({
  response: new Response(null, {
    status,
    headers: retry ? { "Retry-After": retry } : {},
  }),
  data,
});
const prepare = () =>
  prepareCheckout("a@example.com", { error: "" }, new FormData());
const place = (id = 7) =>
  placeCheckout("a@example.com", id, { error: "" }, new FormData());
beforeEach(() => {
  vi.resetAllMocks();
  origin.mockReturnValue("https://shop.example");
  identity.mockResolvedValue({
    owner: "a@example.com",
    token: "fictional-token",
  });
  get.mockResolvedValue(
    response(200, { items: [{ product: { id: 3 }, quantity: 2 }] }),
  );
  post.mockResolvedValue(response(201, { id: 7 }));
});
for (const action of [prepare, place]) {
  it(`${action.name}: rejects foreign origins before accessing identity`, async () => {
    origin.mockReturnValue("https://evil.example");
    expect((await action()).error).toMatch(/Origin/);
    expect(identity).not.toHaveBeenCalled();
  });
  for (const user of [null, { owner: "b@example.com", token: "other" }])
    it(`${action.name}: blocks missing or changed account`, async () => {
      identity.mockResolvedValue(user);
      expect((await action()).error).toMatch(/session changed/);
      expect(post).not.toHaveBeenCalled();
      expect(get).not.toHaveBeenCalled();
    });
}
it("draft uses backend cart quantities and returns review destination", async () => {
  expect(await prepare()).toEqual({ error: "", location: "/orders/7" });
  expect(post).toHaveBeenCalledWith(
    "/api/v1/orders/drafts",
    expect.objectContaining({
      body: { lines: [{ product_id: 3, quantity: 2 }] },
      headers: { Authorization: "Bearer fictional-token" },
    }),
  );
});
for (const status of [401, 429, 503])
  it(`cart read ${status} prevents draft creation`, async () => {
    get.mockResolvedValue(response(status, undefined, "12"));
    const result = await prepare();
    expect(result.error).toBeTruthy();
    expect(post).not.toHaveBeenCalled();
    if (status === 429) expect(result.error).toContain("12");
  });
it("empty cart prevents a draft", async () => {
  get.mockResolvedValue(response(200, { items: [] }));
  expect((await prepare()).error).toMatch(/empty/);
  expect(post).not.toHaveBeenCalled();
});
for (const retry of ["9", "invalid", undefined])
  it(`draft throttling gives safe guidance (${retry})`, async () => {
    post.mockResolvedValue(response(429, undefined, retry));
    expect((await prepare()).error).toMatch(/wait|try again/i);
    expect(post).toHaveBeenCalledTimes(1);
  });
it("draft rejection and lost response remain distinct", async () => {
  post.mockResolvedValue(response(409));
  expect((await prepare()).error).toMatch(/Review your cart/);
  post.mockRejectedValue(new Error("sensitive"));
  expect((await prepare()).error).toMatch(/Check order history/);
});
for (const id of [0, -1, 1.5, NaN, 2147483648])
  it(`rejects invalid placement ${id}`, async () => {
    expect((await place(id)).error).toBe("Invalid order.");
    expect(post).not.toHaveBeenCalled();
  });
it("lost placement response and deliberate retry use exactly the same customer-scoped key", async () => {
  post
    .mockRejectedValueOnce(new Error("lost response"))
    .mockResolvedValue(response(200, { id: 7 }));
  expect((await place()).error).toMatch(/Retry this same order/);
  expect(post).toHaveBeenCalledTimes(1);
  expect(refresh).not.toHaveBeenCalled();
  expect(await place()).toEqual({ error: "", location: "/orders/7" });
  expect(post.mock.calls[0]).toEqual(post.mock.calls[1]);
  expect(post.mock.calls[1][1].params.header).toEqual({
    "idempotency-key": "storefront-order-7",
  });
  expect(refresh).toHaveBeenCalledWith("/cart");
});
for (const [status, message] of [
  [401, /unavailable/],
  [404, /unavailable/],
  [409, /stock changed/],
  [429, /wait|try again/i],
  [503, /Retry this same order/],
] as const)
  it(`placement ${status} has distinct recovery guidance`, async () => {
    post.mockResolvedValue(response(status));
    expect((await place()).error).toMatch(message);
    expect(post).toHaveBeenCalledTimes(1);
    expect(refresh).not.toHaveBeenCalled();
  });
