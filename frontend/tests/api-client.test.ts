import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
import { apiClient } from "../src/lib/api/client";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("server API client", () => {
  it.each([undefined, "https://api.example.test"])(
    "uses the configured origin with uncached bounded requests (%s)",
    async (origin) => {
      vi.stubEnv("API_BASE_URL", origin);
      const signal = new AbortController().signal;
      const timeout = vi.spyOn(AbortSignal, "timeout").mockReturnValue(signal);
      const fetchRequest = vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify([]), {
            headers: { "Content-Type": "application/json" },
          }),
        );
      vi.stubGlobal("fetch", fetchRequest);

      const result = await apiClient().GET("/api/v1/products/");

      expect(result.data).toEqual([]);
      const [request, options] = fetchRequest.mock.calls[0];
      expect(request.url).toBe(
        `${origin ?? "http://127.0.0.1:8000"}/api/v1/products/`,
      );
      expect(request.cache).toBe("no-store");
      expect(request.method).toBe("GET");
      expect(timeout).toHaveBeenCalledWith(5000);
      expect(options.signal).toBe(signal);
    },
  );

  it("propagates transport failures instead of inventing an empty catalog", async () => {
    const failure = new DOMException("Request timed out", "TimeoutError");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(failure));
    await expect(apiClient().GET("/api/v1/products/")).rejects.toBe(failure);
  });
});
