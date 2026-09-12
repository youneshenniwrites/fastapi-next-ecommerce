import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const API = "http://127.0.0.1:18300";

type Product = {
  id: number;
  name: string;
  price: string;
  stock: number;
};

async function products(request: import("@playwright/test").APIRequestContext) {
  const response = await request.get(
    `${API}/api/v1/products/?skip=0&limit=100`,
  );
  expect(response.ok()).toBe(true);
  return (await response.json()) as Product[];
}

async function register(
  request: import("@playwright/test").APIRequestContext,
  email: string,
  password: string,
) {
  const response = await request.post(`${API}/api/v1/auth/register`, {
    data: { email, password },
  });
  expect(response.status()).toBe(201);
}

async function login(
  page: import("@playwright/test").Page,
  email: string,
  password: string,
) {
  await page.goto("/login");
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/#collection$/);
  expect(await page.evaluate(() => document.cookie)).not.toContain("session");
  expect(
    await page.evaluate(() => localStorage.length + sessionStorage.length),
  ).toBe(0);
}

function updateButton(
  page: import("@playwright/test").Page,
  productName: string,
) {
  return page
    .getByRole("form", { name: `Change quantity of ${productName}` })
    .getByRole("button", { name: "Update", exact: true });
}

async function openCartLink(
  page: import("@playwright/test").Page,
  project: string,
) {
  if (/mobile|pixel/i.test(project)) {
    await page.getByRole("button", { name: "Open navigation" }).click();
    await page
      .getByRole("navigation", { name: "Mobile navigation" })
      .getByRole("link", { name: /^Cart/ })
      .click();
  } else {
    await page
      .getByRole("navigation", { name: "Main navigation" })
      .getByRole("link", { name: /^Cart/ })
      .click();
  }
  await expect(page).toHaveURL(/\/cart$/);
}

test("signed-in cart journey persists across reload and logout/login", async ({
  page,
  request,
}, info) => {
  const all = await products(request);
  const item =
    all.find((p) => p.name === "Notebook Set") ?? all.find((p) => p.stock > 5)!;
  const email = `cart-${crypto.randomUUID()}@example.com`;
  const password = "disposable-cart-password";
  await register(request, email, password);

  // Signed-out cart page offers a sign-in action, not private data.
  await page.goto("/cart");
  await expect(
    page.getByRole("heading", { name: "Sign in to view your saved cart" }),
  ).toBeVisible();

  await login(page, email, password);

  await page.goto(`/products/${item.id}`);
  await expect(
    page.getByRole("heading", { name: item.name, exact: true }),
  ).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  const add = page
    .getByRole("main")
    .getByRole("button", { name: /Add to cart|Saved to cart/ });
  await add.focus();
  await expect(add).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByText("Saved.", { exact: false })).toBeVisible();
  const count = page.getByTestId("cart-count").first();
  await expect(count).toHaveText("1");

  // Reload restores the saved cart and count.
  await page.reload();
  await expect(page.getByTestId("cart-count").first()).toHaveText("1");

  await openCartLink(page, info.project.name);
  await expect(page.getByRole("heading", { name: "Your cart." })).toBeVisible();
  await expect(page.getByRole("link", { name: item.name })).toBeVisible();
  const subtotal = page.getByTestId("cart-subtotal");
  await expect(subtotal).toContainText(`£${item.price}`);
  await expect(subtotal).toContainText("GBP");
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);

  // Increase to 2 and confirm the backend-provided subtotal doubles.
  await page
    .getByRole("button", { name: `Increase quantity of ${item.name}` })
    .click();
  await expect(page.getByText("Qty 2")).toBeVisible();
  await expect(page.getByTestId("cart-count").first()).toHaveText("2");
  await page.reload();
  await expect(page.getByText("Qty 2")).toBeVisible();

  // Decrease back to 1, then remove the line.
  await page
    .getByRole("button", { name: `Decrease quantity of ${item.name}` })
    .click();
  await expect(page.getByText("Qty 1")).toBeVisible();
  await page
    .getByRole("button", { name: `Remove ${item.name} from cart` })
    .click();
  await expect(
    page.getByRole("heading", { name: "Your cart is empty" }),
  ).toBeVisible();

  // Re-add, then verify logout/login restores the saved cart.
  await page.goto(`/products/${item.id}`);
  await page
    .getByRole("main")
    .getByRole("button", { name: /Add to cart|Saved to cart/ })
    .click();
  await expect(page.getByTestId("cart-count").first()).toHaveText("1");
  await page.goto("/account");
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.goto("/cart");
  await expect(
    page.getByRole("heading", { name: "Sign in to view your saved cart" }),
  ).toBeVisible();
  await expect(page.getByText(item.name, { exact: true })).toHaveCount(0);
  await login(page, email, password);
  await page.goto("/cart");
  await expect(page.getByRole("link", { name: item.name })).toBeVisible();
  await expect(page.getByTestId("cart-count").first()).toHaveText("1");
});

test("two-account isolation, rapid clicks, invalid quantities, shortages and failures", async ({
  page,
  request,
}, info) => {
  const all = await products(request);
  const first = all.find((p) => p.name === "Notebook Set")!;
  const second = all.find((p) => p.name === "Task Light")!;
  const emailA = `cart-a-${crypto.randomUUID()}@example.com`;
  const emailB = `cart-b-${crypto.randomUUID()}@example.com`;
  const password = "disposable-cart-password";
  await register(request, emailA, password);
  await register(request, emailB, password);

  // Account A saves one product.
  await login(page, emailA, password);
  await page.goto(`/products/${first.id}`);
  await page
    .getByRole("main")
    .getByRole("button", { name: /Add to cart|Saved to cart/ })
    .click();
  await expect(page.getByTestId("cart-count").first()).toHaveText("1");
  await page.goto("/account");
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);

  // Account B starts empty: isolation holds.
  await login(page, emailB, password);
  await openCartLink(page, info.project.name);
  await expect(
    page.getByRole("heading", { name: "Your cart is empty" }),
  ).toBeVisible();
  await page.goto(`/products/${second.id}`);
  await page
    .getByRole("main")
    .getByRole("button", { name: /Add to cart|Saved to cart/ })
    .click();
  await expect(page.getByTestId("cart-count").first()).toHaveText("1");
  await openCartLink(page, info.project.name);
  await expect(page.getByRole("link", { name: second.name })).toBeVisible();
  await expect(page.getByRole("link", { name: first.name })).toHaveCount(0);
  await page.goto("/account");
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);

  // Account A still sees only its own line.
  await login(page, emailA, password);
  await openCartLink(page, info.project.name);
  await expect(page.getByRole("link", { name: first.name })).toBeVisible();
  await expect(page.getByRole("link", { name: second.name })).toHaveCount(0);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);

  // Rapid duplicate submissions collapse into a single write. Keyboard
  // presses dispatch without actionability waits, so the pending disabled
  // button (or the in-flight guard before re-render) swallows the second
  // activation instead of serializing it into a second PUT.
  let writes = 0;
  await page.route("**/api/cart/items/*", async (route) => {
    if (route.request().method() === "PUT") {
      writes++;
      await new Promise((resolve) => setTimeout(resolve, 300));
    }
    await route.continue();
  });
  await page.goto(`/products/${first.id}`);
  const add = page
    .getByRole("main")
    .getByRole("button", { name: /Add to cart|Saved to cart/ });
  await add.focus();
  await page.keyboard.press("Enter");
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("cart-count").first()).toHaveText("2");
  expect(writes).toBe(1);
  await page.unroute("**/api/cart/items/*");

  // Invalid quantities are rejected client-side without any API write, so
  // only the validation message can satisfy this assertion.
  await openCartLink(page, info.project.name);
  const quantity = page.getByLabel(`Quantity of ${first.name}, 1 to 99`);
  await quantity.fill("0");
  await updateButton(page, first.name).click();
  await expect(page.getByRole("alert").first()).toContainText(
    /whole number from 1 to 99/,
  );
  await expect(page).toHaveURL(/\/cart$/);
  await quantity.fill("100");
  await updateButton(page, first.name).click();
  await expect(page.getByRole("alert").first()).toBeVisible();

  // Quantities beyond stock are rejected with a 409 and a stock-specific
  // message (Task Light has stock 8): asserting the status and the message
  // keeps a generic server failure from passing as stock handling.
  await page.goto(`/products/${second.id}`);
  await page
    .getByRole("main")
    .getByRole("button", { name: /Add to cart|Saved to cart/ })
    .click();
  await openCartLink(page, info.project.name);
  const scarce = page.getByLabel(`Quantity of ${second.name}, 1 to 99`);
  await scarce.fill("99");
  const [shortage] = await Promise.all([
    page.waitForResponse(
      (response) =>
        response.url().includes("/api/cart/items/") &&
        response.request().method() === "PUT",
    ),
    updateButton(page, second.name).click(),
  ]);
  expect(shortage.status()).toBe(409);
  await expect(page.getByRole("alert").first()).toContainText(
    /Not enough stock|exceeds current stock/,
  );

  // Failed writes surface the handler's generic recoverable message (the
  // real Next handler never passes backend internals through) and succeed
  // on retry.
  await page.route("**/api/cart/items/*", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: '{"error":"Your cart is temporarily unavailable. Please try again."}',
    }),
  );
  await scarce.fill("2");
  await updateButton(page, second.name).click();
  await expect(page.getByRole("alert").first()).toContainText(
    /temporarily unavailable/,
  );
  await page.unroute("**/api/cart/items/*");
  await updateButton(page, second.name).click();
  await expect(page.getByText("Qty 2").first()).toBeVisible();

  // Concurrent writes to different lines settle to the server state: both
  // increases land, the final UI matches the authoritative cart, and a
  // reload confirms persistence instead of a predated snapshot.
  await Promise.all([
    page
      .getByRole("button", { name: `Increase quantity of ${first.name}` })
      .click(),
    page
      .getByRole("button", { name: `Increase quantity of ${second.name}` })
      .click(),
  ]);
  await expect(page.getByText("Qty 3")).toHaveCount(2);
  await expect(page.getByTestId("cart-count").first()).toHaveText("6");
  await page.reload();
  await expect(page.getByText("Qty 3")).toHaveCount(2);
  await expect(page.getByTestId("cart-count").first()).toHaveText("6");
});

test("switching accounts without sign-out never shows the previous cart", async ({
  page,
  request,
}) => {
  const all = await products(request);
  const first = all.find((p) => p.name === "Notebook Set")!;
  const emailA = `cart-switch-a-${crypto.randomUUID()}@example.com`;
  const emailB = `cart-switch-b-${crypto.randomUUID()}@example.com`;
  const password = "disposable-cart-password";
  await register(request, emailA, password);
  await register(request, emailB, password);

  await login(page, emailA, password);
  await page.goto(`/products/${first.id}`);
  await page
    .getByRole("main")
    .getByRole("button", { name: /Add to cart|Saved to cart/ })
    .click();
  await expect(page.getByTestId("cart-count").first()).toHaveText("1");
  await page.goto("/cart");
  await expect(page.getByRole("link", { name: first.name })).toBeVisible();

  // Fail the new account's re-read: the previous customer's rendered cart
  // must be invalidated (loading, then the error state) instead of preserved
  // with a stale banner.
  await page.route("**/api/cart", (route) => route.abort());
  await page.evaluate(
    async ({ email, password }) => {
      const response = await fetch("/api/session/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok)
        throw new Error(`in-page login failed: ${response.status}`);
    },
    { email: emailB, password },
  );
  // The session provider reloads identity on window focus without remounting
  // the cart provider, exercising the confirmed account-change path.
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(page.getByRole("link", { name: first.name })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
  await page.unroute("**/api/cart");
});

test("stale cart shows a visible warning and recovers on refresh", async ({
  page,
  request,
}) => {
  const all = await products(request);
  const item =
    all.find((p) => p.name === "Notebook Set") ?? all.find((p) => p.stock > 5)!;
  const email = `cart-stale-${crypto.randomUUID()}@example.com`;
  const password = "disposable-cart-password";
  await register(request, email, password);
  await login(page, email, password);
  await page.goto(`/products/${item.id}`);
  await page
    .getByRole("main")
    .getByRole("button", { name: /Add to cart|Saved to cart/ })
    .click();
  await expect(page.getByTestId("cart-count").first()).toHaveText("1");
  await page.goto("/cart");
  await expect(page.getByRole("link", { name: item.name })).toBeVisible();

  // A failed background refresh keeps the rendered cart and surfaces a
  // visible warning instead of wiping private UI.
  await page.route("**/api/cart", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: '{"error":"Your cart is temporarily unavailable. Please try again."}',
      });
      return;
    }
    await route.continue();
  });
  const [failedRefresh] = await Promise.all([
    page.waitForResponse(
      (response) =>
        response.url().endsWith("/api/cart") &&
        response.request().method() === "GET",
    ),
    page.evaluate(() => window.dispatchEvent(new Event("focus"))),
  ]);
  expect(failedRefresh.status()).toBe(503);
  const warning = page
    .getByRole("status")
    .filter({ hasText: "Couldn't update your cart" });
  await expect(warning).toBeVisible();
  await expect(page.getByRole("link", { name: item.name })).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);

  // The next successful refresh clears the warning.
  await page.unroute("**/api/cart");
  const [recoveredRefresh] = await Promise.all([
    page.waitForResponse(
      (response) =>
        response.url().endsWith("/api/cart") &&
        response.request().method() === "GET",
    ),
    page.getByRole("button", { name: "Refresh cart", exact: true }).click(),
  ]);
  expect(recoveredRefresh.ok()).toBe(true);
  await expect(warning).toHaveCount(0);
  await expect(page.getByRole("link", { name: item.name })).toBeVisible();
});

test("mutation timeout shows a recoverable error and reconciles", async ({
  page,
  request,
}) => {
  const all = await products(request);
  const item =
    all.find((p) => p.name === "Notebook Set") ?? all.find((p) => p.stock > 5)!;
  const email = `cart-timeout-${crypto.randomUUID()}@example.com`;
  const password = "disposable-cart-password";
  await register(request, email, password);
  await login(page, email, password);
  await page.goto(`/products/${item.id}`);
  const add = page
    .getByRole("main")
    .getByRole("button", { name: /Add to cart|Saved to cart/ });
  await add.click();
  await expect(page.getByTestId("cart-count").first()).toHaveText("1");

  // Let the server process the write, then delay its response past the
  // 10s client timeout: the aborted request still settles server-side, so
  // the timeout message must appear and reconciliation must converge on
  // the persisted cart.
  await page.route("**/api/cart/items/*", async (route) => {
    if (route.request().method() === "PUT") {
      const upstream = await route.fetch();
      await new Promise((resolve) => setTimeout(resolve, 11000));
      // The client aborts at 10s, so this fulfill is expectedly rejected;
      // the server already processed the write above.
      await route.fulfill({ response: upstream }).catch(() => {});
      return;
    }
    await route.continue();
  });
  await add.click();
  await expect(
    page.getByRole("alert").filter({ hasText: "timed out" }),
  ).toBeVisible({ timeout: 20000 });
  await page.unroute("**/api/cart/items/*");

  // Let the cart page settle once, then wait for client and server to agree
  // again. Navigating inside the poll loop would abort each in-flight
  // re-read with a fresh reload and livelock on the loading state.
  await page.goto("/cart");
  await expect(page.getByText("Qty 2")).toBeVisible({ timeout: 30000 });
  await expect(page.getByTestId("cart-count").first()).toHaveText("2");
});

test("post-write refresh timeout offers a visible retry", async ({
  page,
  request,
}) => {
  const item = (await products(request)).find((product) => product.stock > 5)!;
  const email = `cart-refresh-${crypto.randomUUID()}@example.com`;
  const password = "disposable-cart-password";
  await register(request, email, password);
  await login(page, email, password);
  await page.goto(`/products/${item.id}`);
  await page
    .getByRole("main")
    .getByRole("button", { name: "Add to cart", exact: true })
    .click();
  await expect(page.getByTestId("cart-count").first()).toHaveText("1");
  await page.goto("/cart");
  await expect(page.getByText("Qty 1", { exact: true })).toBeVisible();
  // Leave reads unanswered until the client's real timeout expires.
  await page.route("**/api/cart", () => {});
  await page
    .getByRole("button", { name: `Increase quantity of ${item.name}` })
    .click();
  await expect(
    page.getByRole("button", { name: "Refresh cart", exact: true }),
  ).toBeVisible({ timeout: 15000 });
  await page.unroute("**/api/cart");
  await page.getByRole("button", { name: "Refresh cart", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Refresh cart", exact: true }),
  ).toHaveCount(0);
  await expect(page.getByText("Qty 2", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: `Remove ${item.name} from cart` })
    .click();
  await expect(
    page.getByRole("heading", { name: "Your cart is empty" }),
  ).toBeVisible();
  // An empty saved cart can be stale too (for example, another tab added a line).
  await page.route("**/api/cart", (route) =>
    route.fulfill({ status: 503, body: "{}" }),
  );
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(
    page.getByRole("button", { name: "Refresh cart", exact: true }),
  ).toBeVisible();
  await page.unroute("**/api/cart");
  await page.getByRole("button", { name: "Refresh cart", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Refresh cart", exact: true }),
  ).toHaveCount(0);
});

test("cart retry recovers a failed session check", async ({
  page,
  request,
}) => {
  const email = `cart-session-retry-${crypto.randomUUID()}@example.com`;
  const password = "disposable-cart-password";
  await register(request, email, password);
  await login(page, email, password);
  await page.route("**/api/session/me", (route) =>
    route.fulfill({ status: 503, body: "{}" }),
  );
  await page.goto("/cart");
  await expect(
    page.getByRole("button", { name: "Try again", exact: true }),
  ).toBeVisible();
  await page.unroute("**/api/session/me");
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Your cart is empty" }),
  ).toBeVisible();
});
