import { afterEach, beforeEach, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { NextRequest } from "next/server";
import { login, register } from "../src/lib/session";

const release = "a".repeat(40);
const evidence = {
  "X-Vindor-Limiter-Instance": "b".repeat(32),
  "X-Vindor-Limiter-Sequence": "2",
  "X-Vindor-Limiter-Limit": "60",
  "X-Vindor-Limiter-Context": "verified",
  "X-Vindor-Limiter-Release": release,
};
function request() {
  return new NextRequest("https://shop.test/api/session/login", {
    method: "POST",
    headers: {
      Origin: "https://shop.test",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email: "test@example.test", password: "Test1234!" }),
  });
}
function upstream(status: number, headers = evidence) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response("{}", {
        status,
        headers: {
          ...headers,
          "Retry-After": "12",
          "X-Private": "fictional-secret",
        },
      }),
    ),
  );
}
beforeEach(() => {
  vi.stubEnv("APP_ORIGIN", "https://shop.test");
  vi.stubEnv("APP_ORIGIN_ALIASES", "");
  vi.stubEnv("VERCEL", "1");
  vi.stubEnv("SENTRY_ENVIRONMENT", "development");
  vi.stubEnv("SENTRY_RELEASE", release);
  vi.stubEnv("RATE_LIMIT_DIAGNOSTICS_ENABLED", "true");
});
afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});
it.each([401, 429])(
  "relays only complete matching development evidence on %s",
  async (status) => {
    upstream(status);
    const result = await login(request());
    for (const [name, value] of Object.entries(evidence))
      expect(result.headers.get(name)).toBe(value);
    expect(result.headers.get("Cache-Control")).toContain("no-store");
    expect(result.headers.get("X-Private")).toBeNull();
    if (status === 401)
      expect(result.cookies.get("__Host-session")?.maxAge).toBe(0);
    else expect(result.headers.get("Retry-After")).toBe("12");
  },
);
it.each([
  ["RATE_LIMIT_DIAGNOSTICS_ENABLED", "false"],
  ["SENTRY_ENVIRONMENT", "production"],
  ["VERCEL", ""],
  ["SENTRY_RELEASE", "private-value"],
])("suppresses diagnostics when %s is %s", async (name, value) => {
  vi.stubEnv(name, value);
  upstream(401);
  expect(
    (await login(request())).headers.get("X-Vindor-Limiter-Instance"),
  ).toBeNull();
});
it.each([
  ["X-Vindor-Limiter-Instance", "untrusted-private-value"],
  ["X-Vindor-Limiter-Sequence", "9007199254740992"],
  ["X-Vindor-Limiter-Sequence", "0"],
  ["X-Vindor-Limiter-Limit", "0"],
  ["X-Vindor-Limiter-Context", "private-context"],
  ["X-Vindor-Limiter-Release", "c".repeat(40)],
])("rejects malformed or mismatched %s", async (name, value) => {
  upstream(429, { ...evidence, [name]: value });
  const result = await login(request());
  for (const header of Object.keys(evidence))
    expect(result.headers.get(header)).toBeNull();
});
it("keeps registration outside this diagnostic contract", async () => {
  upstream(429);
  expect(
    (await register(request())).headers.get("X-Vindor-Limiter-Instance"),
  ).toBeNull();
});
