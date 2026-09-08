import { test, expect } from "@playwright/test";
test("real API login, private profile and logout without JS token exposure", async ({
  page,
  request,
}) => {
  const email = `session-${Date.now()}@example.com`;
  const password = "test-only-password-123";
  expect(
    (
      await request.post("http://127.0.0.1:18300/api/v1/auth/register", {
        data: { email, password },
      })
    ).status(),
  ).toBe(201);
  await page.goto("/");
  const login = await page.evaluate(
    async ({ email, password }) => {
      const r = await fetch("/api/session/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      return { status: r.status, body: await r.json() };
    },
    { email, password },
  );
  expect(login).toEqual({ status: 200, body: { authenticated: true } });
  expect(await page.evaluate(() => document.cookie)).not.toContain("session");
  expect(
    await page.evaluate(() => ({
      local: localStorage.length,
      session: sessionStorage.length,
    })),
  ).toEqual({ local: 0, session: 0 });
  const profile = await page.evaluate(async () => {
    const r = await fetch("/api/session/me");
    return {
      status: r.status,
      body: await r.json(),
      cache: r.headers.get("cache-control"),
    };
  });
  expect(profile.status).toBe(200);
  expect(profile.body.email).toBe(email);
  expect(profile.body.access_token).toBeUndefined();
  expect(profile.cache).toContain("no-store");
  expect(
    await page.evaluate(
      async () =>
        (await fetch("/api/session/logout", { method: "POST" })).status,
    ),
  ).toBe(200);
  expect(
    await page.evaluate(async () => (await fetch("/api/session/me")).status),
  ).toBe(401);
  expect(
    (
      await request.post("/api/session/login", { data: { email, password } })
    ).status(),
  ).toBe(403);
});
