import { beforeEach, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
vi.mock("react", () => ({ cache: (fn: unknown) => fn }));
const { identity, get } = vi.hoisted(() => ({
  identity: vi.fn(),
  get: vi.fn(),
}));
vi.mock("@/lib/cart-data", () => ({ cartIdentity: identity }));
vi.mock("@/lib/api/client", () => ({ apiClient: () => ({ GET: get }) }));
import { readOrder, readOrders } from "../src/lib/order-data";
beforeEach(() => {
  vi.resetAllMocks();
  identity.mockResolvedValue({
    owner: "customer@example.com",
    token: "test-token",
  });
});
for (const id of [0, -1, NaN, 1.5, Infinity, 2147483648])
  it(`rejects invalid order ID ${id}`, async () => {
    expect(await readOrder(id)).toEqual({ status: "missing" });
    expect(get).not.toHaveBeenCalled();
  });
for (const list of [true, false]) {
  const read = () => (list ? readOrders(10) : readOrder(7));
  it(`keeps credentials server-side (${list})`, async () => {
    const data = list ? [{ id: 7 }] : { id: 7 };
    get.mockResolvedValue({ response: { status: 200 }, data });
    expect(await read()).toEqual({
      status: "ready",
      owner: "customer@example.com",
      data,
    });
    expect(get.mock.calls[0][1].headers).toEqual({
      Authorization: "Bearer test-token",
    });
  });
  it(`stops before reading without an identity (${list})`, async () => {
    identity.mockResolvedValue(null);
    expect(await read()).toEqual({ status: "guest" });
    expect(get).not.toHaveBeenCalled();
  });
  for (const status of [401, 404, 429, 503])
    it(`handles ${status} (${list})`, async () => {
      get.mockResolvedValue({ response: { status } });
      expect(await read()).toEqual({
        status:
          status === 401
            ? "guest"
            : status === 404 && !list
              ? "missing"
              : "error",
      });
    });
  it(`rejects a missing success body (${list})`, async () => {
    get.mockResolvedValue({ response: { status: 200 } });
    expect(await read()).toEqual({ status: "error" });
  });
  it(`handles network failure (${list})`, async () => {
    get.mockRejectedValue(new Error("private"));
    expect(await read()).toEqual({ status: "error" });
  });
}
it("reads first history page without a cursor", async () => {
  get.mockResolvedValue({ response: { status: 200 }, data: [] });
  expect((await readOrders()).status).toBe("ready");
});

it("fetches one lookahead order after the requested cursor", async () => {
  get.mockResolvedValue({ response: { status: 200 }, data: [] });
  await readOrders(42);
  expect(get).toHaveBeenCalledWith(
    "/api/v1/orders/",
    expect.objectContaining({
      params: { query: { limit: 21, after_id: 42 } },
    }),
  );
});
