import { test, expect } from "@playwright/test";
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
