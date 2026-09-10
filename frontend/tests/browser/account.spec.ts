import { test, expect } from "@playwright/test";
import { createHmac } from "node:crypto";
import AxeBuilder from "@axe-core/playwright";

test("complete UI account journey with duplicate registration and invalid login", async ({
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
  await page.getByRole("link", { name: "Continue to sign in" }).click();
  await expect(page).toHaveURL(/\/login$/);
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
  if (test.info().project.name.includes("Pixel"))
    await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "My account", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Customer profile" }),
  ).toContainText(email);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  expect((await page.request.get("/api/session/me")).status()).toBe(401);
  await page.goto("/account");
  await expect(
    page.getByRole("heading", { name: "Sign in to view your account" }),
  ).toBeVisible();
  await expect(page.getByText(email, { exact: true })).toHaveCount(0);
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

test("background account pages defer all profile requests until visible", async ({
  page,
}) => {
  let requests = 0;
  await page.addInitScript(() =>
    Object.defineProperty(document, "visibilityState", {
      value: "hidden",
      configurable: true,
    }),
  );
  await page.route("**/api/session/me", (route) => {
    requests++;
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        email: "background@example.com",
        created_at: "2026-09-01T12:00:00Z",
      }),
    });
  });
  await page.goto("/account");
  await page.waitForLoadState("networkidle");
  await page.evaluate(() => {
    window.dispatchEvent(new Event("focus"));
    window.dispatchEvent(new PageTransitionEvent("pageshow"));
  });
  expect(requests).toBe(0);
  await expect(
    page.getByText("background@example.com", { exact: true }),
  ).toHaveCount(0);
  await page.evaluate(() => {
    Object.defineProperty(document, "visibilityState", {
      value: "visible",
      configurable: true,
    });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await expect(
    page.getByText("background@example.com", { exact: true }),
  ).toBeVisible();
  expect(requests).toBe(2);
});

for (const mode of ["login", "register"] as const) {
  test(`${mode} waits for delayed scripts before allowing the first submission`, async ({
    page,
  }) => {
    let release!: () => void;
    const scripts = new Promise<void>((resolve) => {
      release = resolve;
    });
    await page.route("**/_next/static/**/*.js", async (route) => {
      await scripts;
      await route.continue();
    });
    let submissions = 0;
    await page.route(`**/api/session/${mode}`, (route) => {
      submissions++;
      return route.fulfill({
        status: 503,
        contentType: "application/json",
        body: "{}",
      });
    });
    try {
      await page.goto(`/${mode}`, { waitUntil: "commit" });
      const email = page.getByLabel("Email address");
      const password = page.getByLabel("Password", { exact: true });
      const submit = page.getByRole("main").getByRole("button");
      await expect(email).toBeDisabled();
      await expect(password).toBeDisabled();
      await expect(submit).toBeDisabled();
      await expect(submit).toContainText("Preparing");
      expect(submissions).toBe(0);
      release();
      await expect(submit).toBeEnabled();
      await email.fill("first-click@example.com");
      await password.fill("fictional-first-click-password");
      let documentRequests = 0;
      page.on("request", (request) => {
        if (
          request.isNavigationRequest() &&
          request.frame() === page.mainFrame()
        )
          documentRequests++;
      });
      await submit.click();
      await expect(page.getByRole("main").getByRole("alert")).toBeVisible();
      expect(submissions).toBe(1);
      expect(documentRequests).toBe(0);
      await expect(page).toHaveURL(new RegExp(`/${mode}$`));
      await expect(email).toHaveValue("first-click@example.com");
    } finally {
      release();
    }
  });
}

test.describe("without JavaScript", () => {
  test.use({ javaScriptEnabled: false });
  test("account forms stay disabled and explain when JavaScript is unavailable", async ({
    page,
  }) => {
    for (const mode of ["login", "register"]) {
      await page.goto(`/${mode}`);
      await expect(page.getByLabel("Email address")).toBeDisabled();
      await expect(page.getByLabel("Password", { exact: true })).toBeDisabled();
      await expect(page.getByRole("main").getByRole("button")).toBeDisabled();
      await expect(
        page.getByText(
          "Loading the form. If this message remains, enable JavaScript and reload the page.",
        ),
      ).toBeVisible();
    }
  });
});

test("guest sign-in links navigate on the first click without reloading", async ({
  page,
}) => {
  for (const source of ["header", "account"]) {
    await page.goto("/account");
    await expect(
      page.getByRole("heading", { name: "Sign in to view your account" }),
    ).toBeVisible();
    if (source === "header" && test.info().project.name.includes("Pixel"))
      await page.getByRole("button", { name: "Open navigation" }).click();
    const signIn =
      source === "account"
        ? page
            .getByRole("main")
            .getByRole("link", { name: "Sign in", exact: true })
        : page.getByRole("link", { name: "Sign in", exact: true }).first();
    let documentRequests = 0;
    const record = (request: import("@playwright/test").Request) => {
      if (request.isNavigationRequest() && request.frame() === page.mainFrame())
        documentRequests++;
    };
    page.on("request", record);
    await signIn.click();
    await expect(
      page.getByRole("heading", { name: "Welcome back." }),
    ).toBeVisible();
    await expect(page.getByLabel("Email address")).toBeEnabled();
    expect(documentRequests).toBe(0);
    page.off("request", record);
  }
});

test("empty and incomplete sign-in submissions stay on the form without requests", async ({
  page,
}) => {
  await page.goto("/login");
  const submit = page.getByRole("button", { name: "Sign in", exact: true });
  const email = page.getByLabel("Email address");
  const password = page.getByLabel("Password", { exact: true });
  await expect(submit).toBeEnabled();
  let documents = 0;
  let loginRequests = 0;
  page.on("request", (request) => {
    if (request.isNavigationRequest() && request.frame() === page.mainFrame())
      documents++;
    if (new URL(request.url()).pathname === "/api/session/login")
      loginRequests++;
  });
  // The owner's exact report: the first click, with both fields untouched.
  await submit.click();
  await expect(email).toBeFocused();
  expect(
    await email.evaluate(
      (el) => (el as HTMLInputElement).validity.valueMissing,
    ),
  ).toBe(true);
  await email.fill("empty-password@example.com");
  await submit.click();
  await expect(password).toBeFocused();
  expect(
    await password.evaluate(
      (el) => (el as HTMLInputElement).validity.valueMissing,
    ),
  ).toBe(true);
  await email.fill("");
  await password.fill("fictional-test-password");
  await submit.click();
  await expect(email).toBeFocused();
  await email.fill("invalid-email");
  await submit.click();
  expect(
    await email.evaluate(
      (el) => (el as HTMLInputElement).validity.typeMismatch,
    ),
  ).toBe(true);
  await expect(page).toHaveURL(/\/login$/);
  expect(documents).toBe(0);
  expect(loginRequests).toBe(0);
});

test("header sign-in on the login page does not reload or discard input", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Email address").fill("navigation@example.com");
  if (test.info().project.name.includes("Pixel"))
    await page.getByRole("button", { name: "Open navigation" }).click();
  let documents = 0;
  page.on("request", (request) => {
    if (request.isNavigationRequest() && request.frame() === page.mainFrame())
      documents++;
  });
  await page.getByRole("link", { name: "Sign in", exact: true }).click();
  await expect(page.getByLabel("Email address")).toBeVisible();
  await expect(page.getByLabel("Email address")).toHaveValue(
    "navigation@example.com",
  );
  await expect(page).toHaveURL(/\/login$/);
  expect(documents).toBe(0);
});
