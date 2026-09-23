import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { POST } from "../src/app/api/payments/webhook/route";
function request(
  body: BodyInit = '{ "event": "fictional" }\n',
  signature = "t=123,v1=fixture",
) {
  return new Request(
    "https://shop.test/api/payments/webhook?url=https://evil.test",
    {
      method: "POST",
      headers: {
        "Stripe-Signature": signature,
        Cookie: "private-session=not-forwarded",
        Authorization: "Bearer not-forwarded",
        "x-vercel-protection-bypass": "caller-controlled-not-forwarded",
      },
      body,
      ...(body instanceof ReadableStream ? { duplex: "half" } : {}),
    },
  );
}
beforeEach(() => {
  vi.stubEnv("STRIPE_WEBHOOK_RELAY_ENABLED", "true");
  vi.stubEnv("API_BASE_URL", "https://private-api.test");
  vi.stubEnv("VERCEL_PROTECTION_BYPASS", "server-only-fixture");
  vi.stubEnv("ALLOW_LOCAL_HTTP_SESSIONS", "false");
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue(
        new Response("upstream-private-body", {
          status: 200,
          headers: {
            "Set-Cookie": "private-cookie",
            "x-secret": "never-forward",
          },
        }),
      ),
  );
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});
describe("Stripe signed webhook relay", () => {
  it("forwards exact bytes and signature only to the fixed backend endpoint", async () => {
    const bytes = new Uint8Array([
      123, 32, 34, 120, 34, 58, 34, 195, 169, 34, 125, 10,
    ]);
    const response = await POST(request(bytes));
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ received: true });
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(response.headers.has("set-cookie")).toBe(false);
    expect(response.headers.has("x-secret")).toBe(false);
    const [url, init] = vi.mocked(fetch).mock.calls[0];
    expect(String(url)).toBe(
      "https://private-api.test/api/v1/payments/webhook",
    );
    expect(init).toMatchObject({
      method: "POST",
      redirect: "error",
      cache: "no-store",
    });
    expect(
      new Uint8Array(await new Response(init?.body).arrayBuffer()),
    ).toEqual(bytes);
    const headers = new Headers(init?.headers);
    expect(headers.get("stripe-signature")).toBe("t=123,v1=fixture");
    expect(headers.get("x-vercel-protection-bypass")).toBe(
      "server-only-fixture",
    );
    expect(headers.has("authorization")).toBe(false);
    expect(headers.has("cookie")).toBe(false);
    expect(String(url)).not.toContain("server-only-fixture");
  });
  it("stays disabled by default", async () => {
    vi.stubEnv("STRIPE_WEBHOOK_RELAY_ENABLED", "");
    expect((await POST(request())).status).toBe(404);
    expect(fetch).not.toHaveBeenCalled();
  });
  it.each(["", " ", "x".repeat(2049)])(
    "rejects absent or oversized signatures",
    async (signature) => {
      expect((await POST(request("{}", signature))).status).toBe(400);
      expect(fetch).not.toHaveBeenCalled();
    },
  );
  it("rejects a missing signature header", async () => {
    expect(
      (
        await POST(
          new Request("https://shop.test/api/payments/webhook", {
            method: "POST",
            body: "{}",
          }),
        )
      ).status,
    ).toBe(400);
    expect(fetch).not.toHaveBeenCalled();
  });
  it("caps chunked bodies independently of content length", async () => {
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(new Uint8Array(256 * 1024));
        controller.enqueue(new Uint8Array(1));
        controller.close();
      },
    });
    expect((await POST(request(body))).status).toBe(413);
    expect(fetch).not.toHaveBeenCalled();
  });
  it("accepts exactly the limit and rejects declared oversized length", async () => {
    expect((await POST(request(new Uint8Array(256 * 1024)))).status).toBe(200);
    vi.mocked(fetch).mockClear();
    const req = request();
    req.headers.set("content-length", String(256 * 1024 + 1));
    expect((await POST(req)).status).toBe(413);
    expect(fetch).not.toHaveBeenCalled();
  });
  it.each([
    "",
    "not-a-url",
    "https://user:secret@api.test",
    "https://api.test/another-path",
    "https://api.test?token=secret",
    "https://api.test#fragment",
    "http://external.test",
    "http://127.0.0.1:8040",
  ])("fails closed on invalid backend configuration %s", async (base) => {
    vi.stubEnv("API_BASE_URL", base);
    const response = await POST(request());
    expect(response.status).toBe(503);
    expect(await response.text()).not.toContain("secret");
    expect(fetch).not.toHaveBeenCalled();
  });
  it("allows explicit loopback and omits unset bypass", async () => {
    vi.stubEnv("API_BASE_URL", "http://127.0.0.1:8040/");
    vi.stubEnv("ALLOW_LOCAL_HTTP_SESSIONS", "true");
    vi.stubEnv("VERCEL_PROTECTION_BYPASS", "");
    expect((await POST(request())).status).toBe(200);
    expect(
      new Headers(vi.mocked(fetch).mock.calls[0][1]?.headers).has(
        "x-vercel-protection-bypass",
      ),
    ).toBe(false);
  });
  it.each([400, 401, 409, 413, 429, 500, 503])(
    "preserves backend failure status %s without body leakage",
    async (status) => {
      vi.mocked(fetch).mockResolvedValue(
        new Response("private diagnostic", { status }),
      );
      const response = await POST(request());
      expect(response.status).toBe(status);
      expect(await response.text()).not.toContain("private diagnostic");
    },
  );
  it("rejects redirects and sanitizes transport exceptions", async () => {
    vi.mocked(fetch).mockRejectedValue(
      new Error("redirect to SSO with private-token"),
    );
    const response = await POST(request());
    expect(response.status).toBe(503);
    expect(await response.text()).not.toContain("private-token");
    expect(vi.mocked(fetch).mock.calls[0][1]?.redirect).toBe("error");
    vi.mocked(fetch).mockResolvedValue(new Response(null, { status: 302 }));
    expect((await POST(request())).status).toBe(502);
  });
  it("bounds upstream waiting even if transport ignores abort", async () => {
    vi.useFakeTimers();
    vi.mocked(fetch).mockImplementation(() => new Promise(() => {}));
    const result = POST(request());
    await vi.advanceTimersByTimeAsync(5001);
    expect((await result).status).toBe(503);
    expect(vi.mocked(fetch).mock.calls[0][1]?.signal?.aborted).toBe(true);
  });
  it("bounds and cancels a stalled incoming stream", async () => {
    vi.useFakeTimers();
    const cancel = vi.fn();
    const result = POST(request(new ReadableStream({ cancel })));
    await vi.advanceTimersByTimeAsync(5001);
    expect((await result).status).toBe(503);
    expect(cancel).toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalled();
  });
});
