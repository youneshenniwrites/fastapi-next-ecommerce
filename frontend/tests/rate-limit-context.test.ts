import { createHmac } from "node:crypto";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { rateLimitContextHeaders } from "../src/lib/rate-limit-context";
import { NextRequest } from "next/server";
import { login, register } from "../src/lib/session";

const secret = "fictional-proxy-key-for-tests-only-123456";
const path = "/api/v1/auth/login";
function request(ip?: string) {
  return new NextRequest("https://shop.test/api/session/login", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      origin: "https://shop.test",
      ...(ip === undefined ? {} : { "x-forwarded-for": ip }),
      "x-vindor-client-context": "caller-forged-context",
    },
    body: JSON.stringify({ email: "demo@example.test", password: "password" }),
  });
}
beforeEach(() => {
  vi.stubEnv("VERCEL", "1");
  vi.stubEnv("RATE_LIMIT_PROXY_SECRET", secret);
  vi.spyOn(Date, "now").mockReturnValue(1_800_000_000_999);
});
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});
it("signs an opaque bucket bound to timestamp, method and exact route", () => {
  const context = rateLimitContextHeaders(request("192.0.2.1"), path)[
    "x-vindor-client-context"
  ];
  expect(context).toBe(
    "1800000000.55b19a7aed1fa105f88a285ebd06541f859396e72dd886ce556c7d8e75f426b8.e5c9832120ac751fd7ecd04563f9cba444539e8164840ec8180356b490c76dc0",
  );
  const [timestamp, bucket, signature] = context.split(".");
  expect(timestamp).toBe("1800000000");
  expect(bucket).toBe(
    createHmac("sha256", secret)
      .update("vindor-client:192.0.2.1")
      .digest("hex"),
  );
  expect(signature).toBe(
    createHmac("sha256", secret)
      .update(`${timestamp}\n${bucket}\nPOST\n${path}`)
      .digest("hex"),
  );
  expect(context).not.toContain("192.0.2.1");
  expect(context).not.toContain(secret);
  expect(rateLimitContextHeaders(request("192.0.2.2"), path)).not.toEqual(
    rateLimitContextHeaders(request("192.0.2.1"), path),
  );
  const other = rateLimitContextHeaders(
    request("192.0.2.1"),
    "/api/v1/auth/register",
  )["x-vindor-client-context"].split(".");
  expect(other[1]).toBe(bucket);
  expect(other[2]).not.toBe(signature);
});
it("canonicalizes equivalent IPv6 addresses into one bucket", () => {
  expect(
    rateLimitContextHeaders(request("2001:0DB8:0:0:0:0:0:1"), path),
  ).toEqual(rateLimitContextHeaders(request("2001:db8::1"), path));
});
it.each([undefined, "", "1", " ".repeat(32), `${secret} `])(
  "omits context for invalid key %s",
  (value) => {
    vi.stubEnv("RATE_LIMIT_PROXY_SECRET", value);
    expect(rateLimitContextHeaders(request("192.0.2.1"), path)).toEqual({});
  },
);
it.each([undefined, "0", "true"])(
  "ignores forwarding headers outside Vercel (%s)",
  (value) => {
    vi.stubEnv("VERCEL", value);
    expect(rateLimitContextHeaders(request("192.0.2.1"), path)).toEqual({});
  },
);
it.each([
  undefined,
  "",
  "invalid",
  "192.0.2.1, 192.0.2.2",
  "[2001:db8::1]",
  "fe80::1%eth0",
])("rejects ambiguous platform identity %s", (ip) => {
  expect(rateLimitContextHeaders(request(ip), path)).toEqual({});
});
it.each([
  [login, "/api/v1/auth/login", 200],
  [register, "/api/v1/auth/register", 201],
] as const)(
  "sends server-created context only upstream from %s",
  async (handler, route, status) => {
    vi.stubEnv("APP_ORIGIN", "https://shop.test");
    vi.stubEnv("APP_ORIGIN_ALIASES", "");
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          access_token: "fictional-token",
          token_type: "bearer",
          expires_in: 1800,
        }),
        { status, headers: { "content-type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const input = request("192.0.2.1");
    const response = await handler(input);
    expect(response.status).toBe(status);
    const upstream = fetchMock.mock.calls[0][0] as Request;
    expect(upstream.headers.get("x-vindor-client-context")).toBe(
      rateLimitContextHeaders(input, route)["x-vindor-client-context"],
    );
    expect(upstream.headers.has("x-forwarded-for")).toBe(false);
    expect(response.headers.has("x-vindor-client-context")).toBe(false);
    expect(await response.text()).not.toContain(secret);
  },
);
