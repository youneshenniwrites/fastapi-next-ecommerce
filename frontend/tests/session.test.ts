import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { NextRequest } from "next/server";
import { login, logout, profile } from "../src/lib/session";
const token = "private-bearer-token";
function request(
  body: unknown = { email: "demo@example.test", password: "password" },
  origin: string | null = "https://shop.test",
) {
  return new NextRequest("https://shop.test/api/session/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(origin ? { Origin: origin } : {}),
    },
    body: JSON.stringify(body),
  });
}
function upstream(body: unknown, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
}
beforeEach(() => {
  vi.stubEnv("APP_ORIGIN", "https://shop.test");
  vi.stubEnv("APP_ORIGIN_ALIASES", "");
  upstream({ access_token: token, token_type: "bearer", expires_in: 1800 });
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});
describe("browser session boundary", () => {
  it("keeps tokens only in host-only secure HttpOnly cookies", async () => {
    const res = await login(request());
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ authenticated: true });
    const cookie = res.cookies.get("__Host-session")!;
    expect(cookie.value).toBe(token);
    expect(cookie).toMatchObject({
      httpOnly: true,
      secure: true,
      sameSite: "lax",
      path: "/",
    });
    expect(cookie.domain).toBeUndefined();
    expect(cookie.maxAge).toBeLessThan(1800);
    expect(res.headers.get("cache-control")).toContain("no-store");
    const call = vi.mocked(fetch).mock.calls[0][0] as Request;
    expect(call.redirect).toBe("error");
    expect(call.headers.get("content-type")).toContain(
      "application/x-www-form-urlencoded",
    );
    expect(await call.text()).toContain("username=demo%40example.test");
  });
  it.each([null, "https://evil.test", "null"])(
    "rejects origin %s before upstream access",
    async (origin) => {
      expect((await login(request(undefined, origin))).status).toBe(403);
      expect((await logout(request(undefined, origin))).status).toBe(403);
      expect(fetch).not.toHaveBeenCalled();
    },
  );
  it.each(["https://evil.test", "//evil.test", "/account", "\\evil"])(
    "rejects all supplied redirect destinations: %s",
    async (next) => {
      expect(
        (await login(request({ email: "a", password: "b", next }))).status,
      ).toBe(400);
      expect(fetch).not.toHaveBeenCalled();
    },
  );
  it("clears invalid credentials but preserves a session on upstream failures", async () => {
    upstream({ detail: "invalid" }, 401);
    expect((await login(request())).cookies.get("__Host-session")?.maxAge).toBe(
      0,
    );
    upstream({ detail: "unavailable" }, 500);
    const failed = await login(request());
    expect(failed.status).toBe(503);
    expect(failed.headers.get("set-cookie")).toBeNull();
  });
  it("returns only the profile and forwards the bearer server-side", async () => {
    upstream({
      id: 1,
      email: "demo@example.test",
      is_active: true,
      is_admin: false,
    });
    const res = await profile(
      new NextRequest("https://shop.test/api/session/me", {
        headers: { cookie: `__Host-session=${token}` },
      }),
    );
    expect(res.status).toBe(200);
    expect(JSON.stringify(await res.json())).not.toContain(token);
    expect(
      (vi.mocked(fetch).mock.calls[0][0] as Request).headers.get(
        "authorization",
      ),
    ).toBe(`Bearer ${token}`);
    expect(res.headers.get("cache-control")).toContain("no-store");
  });
  it("handles missing, expired, malformed and disabled-user sessions as unauthorized", async () => {
    expect(
      (await profile(new NextRequest("https://shop.test/api/session/me")))
        .status,
    ).toBe(401);
    expect(fetch).not.toHaveBeenCalled();
    for (const invalid of ["expired", "malformed", "disabled-user"]) {
      upstream({ detail: "invalid" }, 401);
      const res = await profile(
        new NextRequest("https://shop.test/api/session/me", {
          headers: { cookie: `__Host-session=${invalid}` },
        }),
      );
      expect(res.status).toBe(401);
      expect(res.cookies.get("__Host-session")?.maxAge).toBe(0);
    }
  });
  it("deletes the same cookie on logout", async () => {
    const res = await logout(request());
    expect(res.cookies.get("__Host-session")).toMatchObject({
      maxAge: 0,
      path: "/",
      secure: true,
      httpOnly: true,
    });
  });
  it("bounds upstream requests and hides timeout details", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new DOMException("secret", "TimeoutError")),
    );
    const res = await login(request());
    expect(res.status).toBe(503);
    expect(await res.text()).not.toContain("secret");
    expect(vi.mocked(fetch).mock.calls[0][1]?.signal).toBeInstanceOf(
      AbortSignal,
    );
    const p = await profile(
      new NextRequest("https://shop.test/api/session/me", {
        headers: { cookie: "__Host-session=x" },
      }),
    );
    expect(p.status).toBe(503);
    expect(p.headers.get("set-cookie")).toBeNull();
  });
  it("requires explicit local mode and never downgrades non-loopback HTTP", async () => {
    vi.stubEnv("APP_ORIGIN", "http://127.0.0.1:3000");
    expect(
      (await login(request(undefined, "http://127.0.0.1:3000"))).status,
    ).toBe(503);
    vi.stubEnv("ALLOW_LOCAL_HTTP_SESSIONS", "true");
    const res = await login(request(undefined, "http://127.0.0.1:3000"));
    expect(res.cookies.get("local-session")).toMatchObject({
      secure: false,
      httpOnly: true,
    });
    vi.stubEnv("APP_ORIGIN", "http://shop.test");
    expect((await login(request(undefined, "http://shop.test"))).status).toBe(
      503,
    );
  });
  it.each([0, -1, null, "invalid"])(
    "does not store invalid lifetime %s",
    async (expires_in) => {
      upstream({ access_token: token, token_type: "bearer", expires_in });
      expect((await login(request())).status).toBe(503);
    },
  );
});

it("rejects malformed requests without contacting FastAPI", async () => {
  for (const body of [
    null,
    {},
    { email: "", password: "x" },
    { email: "x", password: "" },
  ])
    expect((await login(request(body))).status).toBe(400);
  expect(
    (
      await login(
        new NextRequest("https://shop.test", {
          method: "POST",
          headers: { origin: "https://shop.test" },
        }),
      )
    ).status,
  ).toBe(415);
  expect(
    (
      await login(
        new NextRequest("https://shop.test", {
          method: "POST",
          headers: {
            origin: "https://shop.test",
            "content-type": "application/json",
          },
          body: "{",
        }),
      )
    ).status,
  ).toBe(400);
  expect(fetch).not.toHaveBeenCalled();
});
it("fails closed for absent or non-canonical configuration", async () => {
  for (const origin of ["", "https://shop.test/", "invalid"]) {
    vi.stubEnv("APP_ORIGIN", origin);
    expect((await login(request())).status).toBe(503);
    expect((await logout(request())).status).toBe(503);
  }
});
it("preserves profile cookies on upstream server errors", async () => {
  upstream({}, 500);
  const res = await profile(
    new NextRequest("https://shop.test", {
      headers: { cookie: "__Host-session=x" },
    }),
  );
  expect(res.status).toBe(503);
  expect(res.headers.get("set-cookie")).toBeNull();
});

it("accepts only explicitly configured HTTPS migration aliases", async () => {
  vi.stubEnv("APP_ORIGIN_ALIASES", '["https://new-shop.test"]');
  expect(
    (await login(request(undefined, "https://new-shop.test"))).status,
  ).toBe(200);
  expect(
    (await logout(request(undefined, "https://new-shop.test"))).status,
  ).toBe(200);
  upstream({ access_token: token, token_type: "bearer", expires_in: 1800 });
  expect((await login(request())).status).toBe(200);
  vi.mocked(fetch).mockClear();
  for (const origin of [
    "https://new-shop.test.evil.test",
    "https://other.test",
    null,
  ]) {
    expect((await login(request(undefined, origin))).status).toBe(403);
    expect((await logout(request(undefined, origin))).status).toBe(403);
  }
  expect(fetch).not.toHaveBeenCalled();
});
it.each([
  "invalid",
  "null",
  '"https://new-shop.test"',
  "[42]",
  '["https://user:pass@shop.test"]',
  '["https://shop.test/path"]',
  '["http://shop.test"]',
  '["invalid"]',
  JSON.stringify(Array(6).fill("https://shop.test")),
])("fails closed for invalid aliases: %s", async (aliases) => {
  vi.stubEnv("APP_ORIGIN_ALIASES", aliases);
  expect((await login(request())).status).toBe(503);
  expect((await logout(request())).status).toBe(503);
  expect(fetch).not.toHaveBeenCalled();
});
it("rejects aliases in local HTTP mode", async () => {
  vi.stubEnv("APP_ORIGIN", "http://127.0.0.1:3000");
  vi.stubEnv("ALLOW_LOCAL_HTTP_SESSIONS", "true");
  vi.stubEnv("APP_ORIGIN_ALIASES", '["https://new-shop.test"]');
  expect((await login(request())).status).toBe(503);
});
