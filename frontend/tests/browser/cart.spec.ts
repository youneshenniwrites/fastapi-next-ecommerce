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

async function fault(
  page: import("@playwright/test").Page,
  request: import("@playwright/test").APIRequestContext,
  settings: Record<string, string>,
) {
  const token = (await page.context().cookies()).find(
    (cookie) => cookie.name === "local-session",
  )?.value;
  expect(token).toBeTruthy();
  const response = await request.post(`${API}/__test/cart-fault`, {
    data: { token, fault: settings },
  });
  expect(response.ok()).toBe(true);
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
  await page.route("**/*", async (route) => {
    if (route.request().headers()["next-action"]) {
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
  await page.unroute("**/*");

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
  await updateButton(page, second.name).click();
  await expect(page.getByRole("alert").first()).toContainText(
    /Not enough stock|exceeds current stock/,
  );

  // Failed writes surface the handler's generic recoverable message (the
  // real Next handler never passes backend internals through) and succeed
  // on retry.
  await fault(page, request, { write: "fail" });
  await scarce.fill("2");
  await updateButton(page, second.name).click();
  await expect(page.getByRole("alert").first()).toContainText(
    /temporarily unavailable/,
  );
  await fault(page, request, {});
  await updateButton(page, second.name).click();
  await expect(page.getByText("Qty 2", { exact: true })).toHaveCount(2);

  // Concurrent writes to different lines settle to the server state: both
  // increases land, the final UI matches the authoritative cart, and a
  // reload confirms persistence instead of a predated snapshot.
  // Dispatch distinct controls without racing Playwright's single mouse pointer.
  await Promise.all([
    page
      .getByRole("button", { name: `Increase quantity of ${first.name}` })
      .evaluate((button) => (button as HTMLButtonElement).click()),
    page
      .getByRole("button", { name: `Increase quantity of ${second.name}` })
      .evaluate((button) => (button as HTMLButtonElement).click()),
  ]);
  await expect(page.getByText("Qty 3")).toHaveCount(2);
  await expect(page.getByTestId("cart-count").first()).toHaveText("6");
  await page.reload();
  await expect(page.getByText("Qty 3")).toHaveCount(2);
  await expect(page.getByTestId("cart-count").first()).toHaveText("6");
});

test("a stale cart cannot write into a different signed-in account", async ({
  page,
  request,
}) => {
  const item = (await products(request)).find(
    (p) => p.name === "Notebook Set",
  )!;
  const emailA = `cart-a-${crypto.randomUUID()}@example.com`;
  const emailB = `cart-b-${crypto.randomUUID()}@example.com`;
  const password = "disposable-cart-password";
  await register(request, emailA, password);
  await register(request, emailB, password);
  await login(page, emailA, password);
  await page.goto(`/products/${item.id}`);
  await page
    .getByRole("main")
    .getByRole("button", { name: "Add to cart", exact: true })
    .click();
  await expect(page.getByTestId("cart-count").first()).toHaveText("1");
  await page.goto("/cart");
  await expect(
    page
      .getByRole("link", {
        name: "My account",
        exact: true,
        includeHidden: true,
      })
      .first(),
  ).toHaveAttribute("href", "/account");
  await expect(
    page.getByRole("button", { name: `Increase quantity of ${item.name}` }),
  ).toBeEnabled();
  // Change the cookie without notifying React, as another window can do.
  await page.evaluate(
    async ({ email, password }) => {
      const response = await fetch("/api/session/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) throw new Error("fixture login failed");
    },
    { email: emailB, password },
  );
  // Intentionally activate the OLD enabled control. Server authorization must
  // reject this even without client focus/visibility protection.
  await page
    .getByRole("button", { name: `Increase quantity of ${item.name}` })
    .click();
  await expect(
    page.getByRole("heading", { name: "Your cart is empty" }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: item.name })).toHaveCount(0);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Your cart is empty" }),
  ).toBeVisible();
  await login(page, emailA, password);
  await page.goto("/cart");
  await expect(page.getByText("Qty 1", { exact: true })).toBeVisible();
});

test("failed new-account reads never preserve the previous cart", async ({
  page,
  request,
}) => {
  const item = (await products(request)).find(
    (p) => p.name === "Notebook Set",
  )!;
  const password = "disposable-cart-password";
  const emailA = `cart-old-${crypto.randomUUID()}@example.com`;
  const emailB = `cart-new-${crypto.randomUUID()}@example.com`;
  await register(request, emailA, password);
  await register(request, emailB, password);
  await login(page, emailA, password);
  await page.goto(`/products/${item.id}`);
  await page
    .getByRole("main")
    .getByRole("button", { name: "Add to cart", exact: true })
    .click();
  await expect(page.getByTestId("cart-count").first()).toHaveText("1");
  await page.goto("/cart");
  await page.evaluate(
    async ({ email, password }) => {
      const response = await fetch("/api/session/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) throw new Error("fixture login failed");
    },
    { email: emailB, password },
  );
  await fault(page, request, { read: "fail", identity: "delay" });
  await page.evaluate(() => {
    window.dispatchEvent(new Event("focus"));
    document
      .querySelector<HTMLButtonElement>(
        'button[aria-label^="Increase quantity"]',
      )
      ?.click();
  });
  await expect(page.getByRole("link", { name: item.name })).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Try again", exact: true }),
  ).toBeVisible();
  await fault(page, request, {});
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Your cart is empty" }),
  ).toBeVisible();
});

async function savedCart(
  page: import("@playwright/test").Page,
  request: import("@playwright/test").APIRequestContext,
) {
  const item = (await products(request)).find(
    (p) => p.name === "Notebook Set",
  )!;
  const email = `cart-${crypto.randomUUID()}@example.com`;
  const password = "disposable-cart-password";
  await register(request, email, password);
  await login(page, email, password);
  await page.goto(`/products/${item.id}`);
  await page
    .getByRole("main")
    .getByRole("button", { name: "Add to cart", exact: true })
    .click();
  await expect(page.getByTestId("cart-count").first()).toHaveText("1");
  return item;
}

test("same-account failed reads keep a visible warning and recover", async ({
  page,
  request,
}) => {
  const item = await savedCart(page, request);
  await page.goto("/cart");
  await expect(
    page.getByRole("button", { name: `Increase quantity of ${item.name}` }),
  ).toBeEnabled();
  await fault(page, request, { read: "fail" });
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  const warning = page
    .getByRole("status")
    .filter({ hasText: "Couldn't update your cart" });
  await expect(warning).toBeVisible();
  await expect(page.getByRole("link", { name: item.name })).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await fault(page, request, {});
  await page.getByRole("button", { name: "Refresh cart", exact: true }).click();
  await expect(warning).toHaveCount(0);
  await expect(page.getByRole("link", { name: item.name })).toBeVisible();
});

test("committed-write timeout recovers without duplicating the add", async ({
  page,
  request,
}) => {
  const item = await savedCart(page, request);
  await fault(page, request, { write: "timeout-after" });
  await page
    .getByRole("main")
    .getByRole("button", { name: /Add to cart|Saved to cart/ })
    .click();
  await expect(page.getByTestId("cart-count").first()).toHaveText("2", {
    timeout: 15000,
  });
  await expect(
    page
      .getByRole("main")
      .getByRole("button", { name: /Add to cart|Saved to cart/ }),
  ).toBeEnabled();
  await expect(
    page.getByRole("button", { name: "Refresh cart", exact: true }),
  ).toHaveCount(0);
  await fault(page, request, {});
  await expect(
    page.getByRole("alert").filter({ hasText: "couldn't confirm" }),
  ).toHaveCount(0);
  await page.goto("/cart");
  await expect(page.getByText("Qty 2", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: item.name })).toBeVisible();
});

test("uncertain writes stay read-only until the cart can be read again", async ({
  page,
  request,
}) => {
  await savedCart(page, request);
  await fault(page, request, {
    write: "timeout-after",
    read: "fail-after-write",
  });
  const add = page
    .getByRole("main")
    .getByRole("button", { name: /Add to cart|Saved to cart/ });
  await add.click();
  await expect(
    page.getByRole("button", { name: "Refresh cart", exact: true }),
  ).toBeVisible({ timeout: 15000 });
  await expect(add).toBeDisabled();
  await fault(page, request, {});
  await page.getByRole("button", { name: "Refresh cart", exact: true }).click();
  await expect(page.getByTestId("cart-count").first()).toHaveText("2");
  await expect(add).toBeEnabled();
  await expect(
    page.getByRole("alert").filter({ hasText: "couldn't confirm" }),
  ).toHaveCount(0);
});

test("post-write read timeout and empty-cart failures offer retry", async ({
  page,
  request,
}) => {
  const item = await savedCart(page, request);
  await page.goto("/cart");
  await fault(page, request, { read: "timeout-after-write" });
  const actionRequest = page.waitForRequest(
    (r) => Boolean(r.headers()["next-action"]),
    { timeout: 5000 },
  );
  await page
    .getByRole("button", { name: `Increase quantity of ${item.name}` })
    .click();
  await actionRequest;
  await expect(
    page.getByRole("button", { name: "Refresh cart", exact: true }),
  ).toBeVisible({ timeout: 15000 });
  await fault(page, request, {});
  await page.getByRole("button", { name: "Refresh cart", exact: true }).click();
  await expect(page.getByText("Qty 2", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: `Remove ${item.name} from cart` })
    .click();
  await expect(
    page.getByRole("heading", { name: "Your cart is empty" }),
  ).toBeVisible();
  await fault(page, request, { read: "fail" });
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(
    page.getByRole("button", { name: "Refresh cart", exact: true }),
  ).toBeVisible();
  await fault(page, request, {});
  await page.getByRole("button", { name: "Refresh cart", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Refresh cart", exact: true }),
  ).toHaveCount(0);
});

test("cart retry recovers a failed server session check", async ({
  page,
  request,
}) => {
  await savedCart(page, request);
  await fault(page, request, { identity: "fail" });
  await page.goto("/cart");
  await expect(
    page.getByRole("button", { name: "Try again", exact: true }),
  ).toBeVisible();
  await fault(page, request, {});
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(page.getByText("Qty 1", { exact: true })).toBeVisible();
});

test("add uses the latest backend quantity instead of the rendered count", async ({
  page,
  request,
}) => {
  const item = await savedCart(page, request);
  const token = (await page.context().cookies()).find(
    (cookie) => cookie.name === "local-session",
  )!.value;
  // Another client changes the cart while this page still displays quantity one.
  const changed = await request.put(`${API}/api/v1/cart/items/${item.id}`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { quantity: 5 },
  });
  expect(changed.status()).toBe(200);
  await expect(page.getByTestId("cart-count").first()).toHaveText("1");
  await page
    .getByRole("main")
    .getByRole("button", { name: /Add to cart|Saved to cart/ })
    .click();
  await expect(page.getByTestId("cart-count").first()).toHaveText("6");
  await page.reload();
  await expect(page.getByTestId("cart-count").first()).toHaveText("6");
});

test("quantity steps use the latest backend value", async ({
  page,
  request,
}) => {
  const item = await savedCart(page, request);
  await page.goto("/cart");
  const token = (await page.context().cookies()).find(
    (c) => c.name === "local-session",
  )!.value;
  async function otherClient(quantity: number) {
    expect(
      (
        await request.put(`${API}/api/v1/cart/items/${item.id}`, {
          headers: { Authorization: `Bearer ${token}` },
          data: { quantity },
        })
      ).status(),
    ).toBe(200);
  }
  await expect(page.getByText("Qty 1", { exact: true })).toBeVisible();
  await otherClient(5);
  await page
    .getByRole("button", { name: `Increase quantity of ${item.name}` })
    .click();
  await expect(page.getByText("Qty 6", { exact: true })).toBeVisible();
  await otherClient(3);
  await page
    .getByRole("button", { name: `Decrease quantity of ${item.name}` })
    .click();
  await expect(page.getByText("Qty 2", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText("Qty 2", { exact: true })).toBeVisible();
});

test("server-rendered cart is private and cannot submit before hydration", async ({
  page,
  request,
  browser,
}) => {
  const item = await savedCart(page, request);
  const cookies = await page.context().cookies();
  const context = await browser.newContext({
    javaScriptEnabled: false,
    baseURL: "http://127.0.0.1:3300",
  });
  try {
    await context.addCookies(cookies);
    const serverPage = await context.newPage();
    const response = await serverPage.goto("/cart");
    expect(response!.headers()["cache-control"]).toContain("no-store");
    await expect(
      serverPage.getByRole("link", { name: item.name }),
    ).toBeVisible();
    await expect(
      serverPage.getByLabel(`Quantity of ${item.name}, 1 to 99`),
    ).toBeDisabled();
    await expect(
      serverPage.getByRole("button", {
        name: `Increase quantity of ${item.name}`,
      }),
    ).toBeDisabled();
    await expect(updateButton(serverPage, item.name)).toBeDisabled();
    expect(await response!.text()).not.toContain(
      cookies.find((cookie) => cookie.name === "local-session")!.value,
    );
  } finally {
    await context.close();
  }
});

test("focus refresh conceals private cart until identity is verified", async ({
  page,
  request,
}) => {
  const item = await savedCart(page, request);
  await page.goto("/cart");
  await expect(page.getByText("Qty 1", { exact: true })).toBeVisible();
  await fault(page, request, { identity: "delay" });
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(page.getByRole("link", { name: item.name })).toHaveCount(0);
  await expect(page.getByTestId("cart-count").first()).toHaveCSS(
    "opacity",
    "0",
  );
  await expect(page.getByText("Qty 1", { exact: true })).toBeVisible();
  await fault(page, request, {});
  await page
    .getByRole("button", {
      name: `Increase quantity of ${item.name}`,
    })
    .click();
  await expect(page.getByText("Qty 2", { exact: true })).toBeVisible();
});

test("focus revalidation preserves the activating quantity click", async ({
  page,
  request,
}) => {
  const item = await savedCart(page, request);
  await page.goto("/cart");
  const increase = page.getByRole("button", {
    name: `Increase quantity of ${item.name}`,
  });
  await expect(increase).toBeEnabled();
  await fault(page, request, { identity: "delay" });
  const box = (await increase.boundingBox())!;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(page.getByRole("link", { name: item.name })).toHaveCount(0);
  expect(
    await page.evaluate(() =>
      Boolean(document.activeElement?.closest("[data-cart-private]")),
    ),
  ).toBe(false);
  await page.mouse.up();
  await expect(page.getByText("Qty 2", { exact: true })).toBeVisible();
  await fault(page, request, {});
});

test("focus revalidation preserves the activating add click", async ({
  page,
  request,
}) => {
  const item = await savedCart(page, request);
  const add = page
    .getByRole("main")
    .getByRole("button", { name: "Add to cart", exact: true });
  await page.reload();
  await expect(add).toBeEnabled();
  await fault(page, request, { identity: "delay" });
  const box = (await add.boundingBox())!;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(page.getByTestId("cart-count").first()).toHaveCSS(
    "opacity",
    "0",
  );
  await page.mouse.up();
  await expect(page.getByTestId("cart-count").first()).toHaveText("2");
  await fault(page, request, {});
  await page.goto("/cart");
  await expect(page.getByRole("link", { name: item.name })).toBeVisible();
  await expect(page.getByText("Qty 2", { exact: true })).toBeVisible();
});

test("session poll expiry clears the cart without a focus event", async ({
  page,
  request,
}) => {
  await page.clock.install();
  const item = await savedCart(page, request);
  await page.goto("/cart");
  await expect(page.getByRole("link", { name: item.name })).toBeVisible();
  await page.context().clearCookies();
  await page.clock.fastForward(60001);
  await expect(page.getByRole("link", { name: item.name })).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Sign in to view your saved cart" }),
  ).toBeVisible();
  await expect(page.getByTestId("cart-count")).toHaveCount(0);
});

test("static login content streams while private cart reads are pending", async ({
  page,
  request,
}) => {
  await savedCart(page, request);
  await fault(page, request, { identity: "timeout" });
  await page.goto("/login", { waitUntil: "commit" });
  await expect(
    page.getByRole("heading", { name: "Welcome back." }),
  ).toBeVisible({ timeout: 3000 });
  await fault(page, request, {});
});
