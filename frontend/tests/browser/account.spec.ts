import { test, expect } from "@playwright/test";
import { createHmac } from "node:crypto";
import AxeBuilder from "@axe-core/playwright";

test("accessible registration, duplicate account, invalid login and safe success", async ({
  page,
}) => {
  const email = `account-${crypto.randomUUID()}@example.com`;
  const password = "disposable-test-password";
  await page.goto("/register");
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: `test-results/account-${test.info().project.name}.png`,
  });
  const emailField = page.getByLabel("Email address");
  const passwordField = page.getByLabel("Password", { exact: true });
  await emailField.focus();
  await page.keyboard.press("Tab");
  await expect(passwordField).toBeFocused();
  await emailField.fill(email);
  await passwordField.fill("short");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  expect(
    await passwordField.evaluate(
      (el) => (el as HTMLInputElement).validity.tooShort,
    ),
  ).toBe(true);
  await passwordField.fill(password);
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(
    page.getByText("Your account is ready. Sign in to continue."),
  ).toBeFocused();
  await page.goto("/register");
  await emailField.fill(email);
  await passwordField.fill(password);
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "Try signing in",
  );
  await expect(page.getByRole("main").getByRole("alert")).toBeFocused();
  await page.goto("/login?next=https://attacker.example");
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await emailField.fill(email);
  await passwordField.fill("wrong-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "incorrect",
  );
  await passwordField.fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/#collection$/);
  expect(await page.evaluate(() => document.cookie)).not.toContain("session");
  expect(
    await page.evaluate(async () => (await fetch("/api/session/me")).status),
  ).toBe(200);
  expect(
    await page.evaluate(() => localStorage.length + sessionStorage.length),
  ).toBe(0);
});

test("pending submission prevents duplicates and recovers from a service failure", async ({
  page,
}) => {
  let complete!: () => void;
  const waiting = new Promise<void>((resolve) => {
    complete = resolve;
  });
  let requests = 0;
  await page.route("**/api/session/login", async (route) => {
    requests++;
    await waiting;
    await route.fulfill({
      status: 503,
      contentType: "application/json",
      body: '{"error":"private backend error"}',
    });
  });
  await page.goto("/login");
  await page.getByLabel("Email address").fill("test@example.com");
  await page.getByLabel("Password", { exact: true }).fill("test-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Signing in…" }),
  ).toBeDisabled();
  await expect(page.getByLabel("Email address")).toBeDisabled();
  complete();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "temporarily unavailable",
  );
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeEnabled();
  expect(requests).toBe(1);
  await page.unroute("**/api/session/login");
  await page.route("**/api/session/login", (route) => route.abort());
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "couldn't connect",
  );
});

test("private profile, account navigation and logout on desktop and mobile", async ({
  page,
  request,
}) => {
  const email = `profile-${crypto.randomUUID()}@example.com`;
  const password = "disposable-profile-password";
  await page.goto("/account");
  await expect(
    page.getByRole("heading", { name: "Sign in to view your account" }),
  ).toBeVisible();
  expect(
    (
      await request.post("http://127.0.0.1:18300/api/v1/auth/register", {
        data: { email, password },
      })
    ).status(),
  ).toBe(201);
  await page.goto("/login");
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/#collection$/);
  if (test.info().project.name.includes("Pixel"))
    await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "My account", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Customer profile" }),
  ).toContainText(email);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  const html = await (await page.request.get("/account")).text();
  expect(html).not.toContain(email);
  const me = await page.request.get("/api/session/me");
  expect(me.headers()["cache-control"]).toContain("no-store");
  await page.route("**/api/session/logout", (route) =>
    route.fulfill({ status: 503, body: "{}" }),
  );
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "couldn't confirm sign-out",
  );
  await expect(page.getByText(email, { exact: true })).toBeVisible();
  await page.unroute("**/api/session/logout");
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  expect((await page.request.get("/api/session/me")).status()).toBe(401);
  await page.goBack();
  await expect(page.getByText(email, { exact: true })).toHaveCount(0);
  await page.goto("/account");
  await expect(
    page.getByRole("heading", { name: "Sign in to view your account" }),
  ).toBeVisible();
});

test("expired cookie and unavailable profile never expose cached customer data", async ({
  page,
  context,
}) => {
  const header = Buffer.from(
    JSON.stringify({ alg: "HS256", typ: "JWT" }),
  ).toString("base64url");
  const payload = Buffer.from(JSON.stringify({ sub: "1", exp: 1 })).toString(
    "base64url",
  );
  const signature = createHmac(
    "sha256",
    "browser-tests-only-not-a-production-secret",
  )
    .update(`${header}.${payload}`)
    .digest("base64url");
  await context.addCookies([
    {
      name: "local-session",
      value: `${header}.${payload}.${signature}`,
      url: "http://127.0.0.1:3300",
      httpOnly: true,
      sameSite: "Lax",
    },
  ]);
  await page.goto("/account");
  await expect(
    page.getByRole("heading", { name: "Sign in to view your account" }),
  ).toBeVisible();
  expect(
    (await context.cookies()).some((cookie) => cookie.name === "local-session"),
  ).toBe(false);
  await page.route("**/api/session/me", (route) =>
    route.fulfill({ status: 503, body: "{}" }),
  );
  await page.reload();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "temporarily unavailable",
  );
  await expect(
    page.getByRole("region", { name: "Customer profile" }),
  ).toHaveCount(0);
  await page.unroute("**/api/session/me");
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(
    page.getByRole("heading", { name: "Sign in to view your account" }),
  ).toBeVisible();
});

test("restoring an account page revalidates and discards its previous profile", async ({
  page,
}) => {
  await page.route("**/api/session/me", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        email: "demo@example.com",
        created_at: "2026-09-01T12:00:00Z",
      }),
    }),
  );
  await page.goto("/account");
  await expect(
    page.getByText("demo@example.com", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: `test-results/profile-${test.info().project.name}.png`,
  });
  await page.evaluate(() =>
    window.dispatchEvent(new PageTransitionEvent("pagehide")),
  );
  await expect(page.getByText("demo@example.com", { exact: true })).toHaveCount(
    0,
  );
  await page.unroute("**/api/session/me");
  await page.route("**/api/session/me", (route) =>
    route.fulfill({ status: 401, body: "{}" }),
  );
  await page.evaluate(() =>
    window.dispatchEvent(
      new PageTransitionEvent("pageshow", { persisted: true }),
    ),
  );
  await expect(
    page.getByRole("heading", { name: "Sign in to view your account" }),
  ).toBeVisible();
  await expect(page.getByText("demo@example.com", { exact: true })).toHaveCount(
    0,
  );
});
