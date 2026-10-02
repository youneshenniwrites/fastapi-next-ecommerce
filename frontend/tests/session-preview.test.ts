import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { NextRequest } from "next/server";
import { login, logout, register, sessionPolicy } from "../src/lib/session";

const hostname = "vindor-preview-ab123.vercel.app";
const origin = `https://${hostname}`;
function request(requestOrigin: string | null = origin, host = hostname) {
  return new NextRequest(`https://${host}/api/session/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Host: host,
      "X-Forwarded-Host": host,
      ...(requestOrigin ? { Origin: requestOrigin } : {}),
    },
    body: JSON.stringify({
      email: "preview@example.test",
      password: "fictional-password",
    }),
  });
}

beforeEach(() => {
  vi.stubEnv("APP_ORIGIN_MODE", "vercel-preview");
  vi.stubEnv("VERCEL", "1");
  vi.stubEnv("VERCEL_ENV", "preview");
  vi.stubEnv("VERCEL_URL", hostname);
  vi.stubEnv("APP_ORIGIN", "https://stable-development.test");
  vi.stubEnv("APP_ORIGIN_ALIASES", "invalid unused aliases");
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          access_token: "private-preview-token",
          token_type: "bearer",
          expires_in: 1800,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    ),
  );
});
afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("explicit Vercel preview session origin", () => {
  it("accepts the exact provider origin and retains host-only secure cookies", async () => {
    const response = await login(request());
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ authenticated: true });
    expect(response.cookies.get("__Host-session")).toMatchObject({
      httpOnly: true,
      secure: true,
      sameSite: "lax",
      path: "/",
    });
    expect(response.cookies.get("__Host-session")?.domain).toBeUndefined();
    expect(sessionPolicy().origins).toEqual([origin]);
    const loggedOut = await logout(request());
    expect(loggedOut.status).toBe(200);
    expect(loggedOut.cookies.get("__Host-session")?.maxAge).toBe(0);
  });

  it("permits registration at the same exact preview origin", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response('{"id":1}', {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }),
    );
    expect((await register(request())).status).toBe(201);
    expect(fetch).toHaveBeenCalledOnce();
  });

  it.each([
    null,
    "null",
    "https://stable-development.test",
    "https://other-preview.vercel.app",
    `http://${hostname}`,
    `${origin}:444`,
    `${origin}.evil.test`,
    `${origin}/`,
  ])("rejects %s before contacting the API", async (untrustedOrigin) => {
    for (const handler of [login, register, logout]) {
      const response = await handler(request(untrustedOrigin));
      expect(response.status).toBe(403);
      expect(response.headers.get("set-cookie")).toBeNull();
    }
    expect(fetch).not.toHaveBeenCalled();
  });

  it("does not authorize an origin through Host or forwarded Host", async () => {
    const response = await login(
      request("https://attacker.vercel.app", "attacker.vercel.app"),
    );
    expect(response.status).toBe(403);
    expect(fetch).not.toHaveBeenCalled();
  });

  it.each([
    "",
    "vercel.app",
    "evil.test",
    `${hostname}.evil.test`,
    `nested.${hostname}`,
    `https://${hostname}`,
    `user:password@${hostname}`,
    `${hostname}:443`,
    `${hostname}/`,
    `${hostname}?x=1`,
    `${hostname}#fragment`,
    `*.${hostname}`,
    "PREVIEW.vercel.app",
    ` ${hostname}`,
    `${hostname}\n`,
    "-preview.vercel.app",
    "preview-.vercel.app",
    "preview_host.vercel.app",
    `${"a".repeat(64)}.vercel.app`,
  ])("fails closed for malformed provider hostname %s", async (value) => {
    vi.stubEnv("VERCEL_URL", value);
    vi.stubEnv("APP_ORIGIN", origin);
    vi.stubEnv("APP_ORIGIN_ALIASES", "[]");
    for (const handler of [login, register, logout]) {
      const response = await handler(request());
      expect(response.status).toBe(503);
      expect(response.headers.get("set-cookie")).toBeNull();
    }
    expect(fetch).not.toHaveBeenCalled();
  });

  it.each([
    ["", "preview"],
    ["0", "preview"],
    ["1", ""],
    ["1", "development"],
    ["1", "production"],
  ])(
    "fails closed outside the provider preview context %s/%s",
    async (vercel, environment) => {
      vi.stubEnv("VERCEL", vercel);
      vi.stubEnv("VERCEL_ENV", environment);
      vi.stubEnv("APP_ORIGIN", origin);
      vi.stubEnv("APP_ORIGIN_ALIASES", "[]");
      expect((await login(request())).status).toBe(503);
      expect(fetch).not.toHaveBeenCalled();
    },
  );

  it.each(["preview", "explicit", " vercel-preview", "vercel-preview "])(
    "fails closed for unsupported mode %s",
    async (mode) => {
      vi.stubEnv("APP_ORIGIN_MODE", mode);
      vi.stubEnv("APP_ORIGIN_ALIASES", "[]");
      expect(
        (await login(request("https://stable-development.test"))).status,
      ).toBe(503);
      expect(fetch).not.toHaveBeenCalled();
    },
  );

  it("keeps explicit origin configuration authoritative when preview mode is omitted", async () => {
    vi.stubEnv("APP_ORIGIN_MODE", "");
    vi.stubEnv("APP_ORIGIN_ALIASES", "[]");
    expect((await login(request())).status).toBe(403);
    expect(fetch).not.toHaveBeenCalled();
    expect(
      (await login(request("https://stable-development.test"))).status,
    ).toBe(200);
  });
});
