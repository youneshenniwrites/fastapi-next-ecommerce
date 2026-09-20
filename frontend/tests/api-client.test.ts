import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
import { apiClient } from "../src/lib/api/client";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe("server API client", () => {
  it.each([undefined, "https://api.example.test"])(
    "uses the configured origin with uncached bounded requests (%s)",
    async (origin) => {
      vi.stubEnv("API_BASE_URL", origin);

      const fetchRequest = vi.fn().mockResolvedValue(
        new Response(JSON.stringify([]), {
          headers: { "Content-Type": "application/json" },
        }),
      );
      vi.stubGlobal("fetch", fetchRequest);

      const result = await apiClient().GET("/api/v1/products/");

      expect(result.data).toEqual([]);
      expect(result.response).toBe(await fetchRequest.mock.results[0].value);
      const [request, options] = fetchRequest.mock.calls[0];
      expect(request.url).toBe(
        `${origin ?? "http://127.0.0.1:8000"}/api/v1/products/`,
      );
      expect(request.cache).toBe("no-store");
      expect(request.method).toBe("GET");
      expect(options.signal).toBeInstanceOf(AbortSignal);
      expect(options.signal.aborted).toBe(false);
    },
  );

  it("propagates transport failures instead of inventing an empty catalog", async () => {
    const failure = new DOMException("Request timed out", "TimeoutError");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(failure));
    await expect(apiClient().GET("/api/v1/products/")).rejects.toBe(failure);
  });
});

// The fetch implementation can lose signal propagation through Request copies.
// Deadlines must bound the caller even when the transport ignores cancellation.
describe("complete API response deadline", () => {
  it("rejects an unresponsive transport after five seconds without retrying", async () => {
    vi.useFakeTimers();
    const transport = vi.fn(() => new Promise<Response>(() => {}));
    vi.stubGlobal("fetch", transport);
    const pending = apiClient().GET("/api/v1/products/");
    const rejected = expect(pending).rejects.toMatchObject({
      name: "TimeoutError",
    });
    await vi.advanceTimersByTimeAsync(4999);
    expect(transport).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1);
    await rejected;
    expect(transport).toHaveBeenCalledTimes(1);
    expect(vi.getTimerCount()).toBe(0);
  });
  it("bounds a response whose headers arrive but whose body stalls", async () => {
    vi.useFakeTimers();
    const cancel = vi.fn();
    const stream = new ReadableStream({
      cancel,
      start(c) {
        c.enqueue(new TextEncoder().encode("["));
      },
    });
    const response = new Response(stream, {
      headers: { "Content-Type": "application/json" },
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
    const pending = apiClient().GET("/api/v1/products/");
    const rejected = expect(pending).rejects.toMatchObject({
      name: "TimeoutError",
    });
    await vi.advanceTimersByTimeAsync(5000);
    await rejected;
    expect(fetch).toHaveBeenCalledTimes(1);
    await vi.waitFor(() => expect(cancel).toHaveBeenCalledTimes(1));
    expect(vi.getTimerCount()).toBe(0);
  });
  it("clears its deadline on an ordinary failure", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    await expect(apiClient().GET("/api/v1/products/")).rejects.toThrow(
      "offline",
    );
    expect(vi.getTimerCount()).toBe(0);
  });
});

it("discards a response arriving after the deadline instead of acknowledging it", async () => {
  vi.useFakeTimers();
  let release!: (response: Response) => void;
  vi.stubGlobal(
    "fetch",
    vi.fn(
      () =>
        new Promise<Response>((resolve) => {
          release = resolve;
        }),
    ),
  );
  const pending = apiClient().GET("/api/v1/products/");
  const rejected = expect(pending).rejects.toMatchObject({
    name: "TimeoutError",
  });
  await vi.advanceTimersByTimeAsync(5000);
  await rejected;
  const cancel = vi.fn();
  release(new Response(new ReadableStream({ cancel })));
  await vi.advanceTimersByTimeAsync(0);
  expect(cancel).toHaveBeenCalledTimes(1);
  expect(fetch).toHaveBeenCalledTimes(1);
});

it("does not detach an abort-ignoring write before it commits", async () => {
  vi.useFakeTimers();
  let finish!: (response: Response) => void;
  let committed = false;
  let settled = false;
  vi.stubGlobal(
    "fetch",
    vi.fn(
      () =>
        new Promise<Response>((resolve) => {
          finish = resolve;
        }),
    ),
  );
  const pending = apiClient()
    .PUT("/api/v1/cart/items/{product_id}", {
      params: { path: { product_id: 1 } },
      body: { quantity: 2 },
    })
    .then((result) => {
      settled = true;
      expect(committed).toBe(true);
      return result;
    });
  await vi.advanceTimersByTimeAsync(6000);
  expect(settled).toBe(false);
  expect(fetch).toHaveBeenCalledTimes(1);
  committed = true;
  finish(
    new Response(JSON.stringify({ items: [] }), {
      headers: { "Content-Type": "application/json" },
    }),
  );
  expect((await pending).response.status).toBe(200);
});
