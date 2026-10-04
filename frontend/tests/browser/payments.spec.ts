import { createHmac } from "node:crypto";
import AxeBuilder from "@axe-core/playwright";
import { test, expect } from "./security-fixture";

const API = "http://127.0.0.1:18302";
const ORIGIN = "http://127.0.0.1:3302";

for (const outcome of [
  "paid",
  "cancelled",
  "expired",
  "failed",
  "lost response",
  "processing",
] as const) {
  test(`sandbox checkout reconciles ${outcome} without another order`, async ({
    page,
    request,
  }) => {
    const email = `payment-${crypto.randomUUID()}@example.com`;
    const password = "fictional-payment-password";
    expect(
      (
        await request.post(`${API}/api/v1/auth/register`, {
          data: { email, password },
        })
      ).status(),
    ).toBe(201);
    expect(
      (
        await page.request.post("/api/session/login", {
          headers: { Origin: ORIGIN },
          data: { email, password },
        })
      ).status(),
    ).toBe(200);
    const token = (await page.context().cookies()).find(
      (cookie) => cookie.name === "local-session",
    )!.value;
    const headers = { Authorization: `Bearer ${token}` };
    const products = await (
      await request.get(`${API}/api/v1/products/`)
    ).json();
    const product = products.find((item: { stock: number }) => item.stock > 0);
    expect(
      (
        await request.put(`${API}/api/v1/cart/items/${product.id}`, {
          headers,
          data: { quantity: 1 },
        })
      ).status(),
    ).toBe(200);
    await page.goto("/cart");
    await page
      .getByRole("button", { name: "Review checkout", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Review your order" }),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Place demo order", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Your demo order" }),
    ).toBeVisible();
    const orderId = Number(new URL(page.url()).pathname.split("/").at(-1));
    const orderPath = `/orders/${orderId}`;
    await expect(
      page
        .getByRole("main")
        .getByText("Awaiting sandbox payment", { exact: false }),
    ).toBeVisible();
    expect(
      (await new AxeBuilder({ page }).include("main").analyze()).violations,
    ).toEqual([]);
    // A forged/success return URL is never payment proof.
    await page.goto(`${orderPath}?payment=return`);
    await expect(
      page
        .getByRole("main")
        .getByText("Awaiting sandbox payment", { exact: false }),
    ).toBeVisible();
    if (outcome === "lost response") {
      expect(
        (
          await request.post(`${API}/__test/payment-fault`, {
            data: { order_id: orderId, lose_create_response: true },
          })
        ).status(),
      ).toBe(200);
    }
    // Only the provider navigation is mocked; order/payment APIs and signed webhook are real.
    await page.route("https://checkout.stripe.com/**", (route) =>
      route.fulfill({
        contentType: "text/html",
        body: "<h1>Disposable sandbox provider</h1>",
      }),
    );
    const pay = page.getByRole("button", {
      name: "Pay with Stripe sandbox",
      exact: true,
    });
    await pay.focus();
    await page.keyboard.press("Enter");
    if (outcome === "lost response") {
      await expect(page.getByRole("main").getByRole("alert")).toContainText(
        "Check this order's status",
      );
      await page
        .getByRole("button", { name: "Pay with Stripe sandbox", exact: true })
        .click();
    }
    await expect(
      page.getByRole("heading", { name: "Disposable sandbox provider" }),
    ).toBeVisible();
    if (outcome === "processing") {
      expect(
        (
          await request.post(`${API}/__test/payment-event`, {
            data: { order_id: orderId, state: "processing" },
          })
        ).status(),
      ).toBe(200);
      await page.goto(orderPath);
      await page
        .getByRole("button", { name: "Cancel unpaid order", exact: true })
        .click();
      await expect(page.getByRole("main").getByRole("alert")).toContainText(
        "could not be cancelled",
      );
      const held = await (
        await request.get(`${API}/__test/payment/${orderId}`)
      ).json();
      expect(held.payment_status).toBe("pending");
      expect(held.products[0].reserved_stock).toBe(1);
    }
    if (outcome === "cancelled") {
      await page.goto(`${orderPath}?payment=cancelled`);
      await expect(
        page
          .getByRole("main")
          .getByText("Awaiting sandbox payment", { exact: false }),
      ).toBeVisible();
      await page
        .getByRole("button", { name: "Cancel unpaid order", exact: true })
        .click();
    } else {
      const state =
        outcome === "lost response" || outcome === "processing"
          ? "paid"
          : outcome;
      const event = {
        order_id: orderId,
        state,
        event_id: `evt_browser_${orderId}`,
      };
      expect(
        (
          await request.post(`${API}/__test/payment-event`, { data: event })
        ).status(),
      ).toBe(200);
      expect(
        (
          await request.post(`${API}/__test/payment-event`, { data: event })
        ).status(),
      ).toBe(200);
      await page.goto(`${orderPath}?payment=return`);
    }
    const label =
      outcome === "paid" ||
      outcome === "lost response" ||
      outcome === "processing"
        ? "Paid — sandbox only"
        : outcome === "cancelled"
          ? "Cancelled — stock released"
          : outcome === "expired"
            ? "Expired — stock released"
            : "Payment failed";
    await expect(
      page.getByRole("main").getByText(label, { exact: false }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", {
        name: "Pay with Stripe sandbox",
        exact: true,
      }),
    ).toHaveCount(0);
    const orders = await (
      await request.get(`${API}/api/v1/orders/`, { headers })
    ).json();
    expect(orders).toHaveLength(1);
    const fixture = await (
      await request.get(`${API}/__test/payment/${orderId}`)
    ).json();
    expect(fixture.session_count).toBe(1);
    const currentProducts = await (
      await request.get(`${API}/api/v1/products/`)
    ).json();
    expect(
      currentProducts.find((item: { id: number }) => item.id === product.id)
        .stock,
    ).toBe(product.stock - (label.startsWith("Paid") ? 1 : 0));
    await page
      .getByRole("link", { name: "Order history", exact: true })
      .click();
    await expect(
      page.getByRole("link", {
        name: new RegExp(`Order #${orderId} — ${label}`),
      }),
    ).toBeVisible();
    expect(
      (await new AxeBuilder({ page }).include("main").analyze()).violations,
    ).toEqual([]);
  });
}

test("public relay preserves signed bytes and rejects unsigned requests", async ({
  request,
}) => {
  const body = JSON.stringify({
    id: "evt_relay_fixture",
    livemode: false,
    type: "fixture.noop",
    data: { object: {} },
  });
  const timestamp = Math.floor(Date.now() / 1000);
  const signature = createHmac("sha256", "whsec_browser_fixture_only")
    .update(`${timestamp}.${body}`)
    .digest("hex");
  expect(
    (await request.post("/api/payments/webhook", { data: body })).status(),
  ).toBe(400);
  const accepted = await request.post("/api/payments/webhook", {
    data: body,
    headers: { "Stripe-Signature": `t=${timestamp},v1=${signature}` },
  });
  expect(accepted.status()).toBe(200);
  expect(await accepted.json()).toEqual({ received: true });
});

test("keyboard demo journey keeps catalog, login, cart and sandbox return accessible", async ({
  page,
  request,
}, info) => {
  if (info.project.name.includes("Pixel"))
    await page.setViewportSize({ width: 320, height: 740 });
  const { expectAccessibleLayout, keyboardActivate } =
    await import("./accessibility-helpers");
  const email = `accessibility-${crypto.randomUUID()}@example.com`;
  const password = "fictional-accessibility-password";
  expect(
    (
      await request.post(`${API}/api/v1/auth/register`, {
        data: { email, password },
      })
    ).status(),
  ).toBe(201);
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("12 objects");
  await expectAccessibleLayout(page);
  await keyboardActivate(
    page,
    page.getByRole("link", { name: /Oak Monitor Stand/ }),
  );
  await expect(
    page.getByRole("heading", {
      name: "Oak Monitor Stand",
      level: 1,
      exact: true,
    }),
  ).toBeVisible();
  await expectAccessibleLayout(page);
  await keyboardActivate(
    page,
    page.getByRole("main").getByRole("link", { name: "Sign in to add" }),
  );
  await expect(page.getByLabel("Email address")).toBeEnabled();
  await expectAccessibleLayout(page);
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password", { exact: true }).fill("incorrect-password");
  await keyboardActivate(
    page,
    page.getByRole("button", { name: "Sign in", exact: true }),
  );
  const alert = page.getByRole("main").getByRole("alert");
  await expect(alert).toContainText("incorrect");
  await expect(alert).toBeFocused();
  await expectAccessibleLayout(page);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await keyboardActivate(
    page,
    page.getByRole("button", { name: "Sign in", exact: true }),
  );
  await expect(page).toHaveURL(/\/#collection$/);
  await page.goto("/products/1");
  await keyboardActivate(
    page,
    page.getByRole("button", { name: "Add to cart", exact: true }),
  );
  await expect(page.getByRole("main").getByRole("status")).toContainText(
    "Saved",
  );
  await keyboardActivate(
    page,
    page.getByRole("link", { name: "View your cart", exact: true }),
  );
  await expect(
    page.getByRole("heading", { name: "Your cart.", exact: true }),
  ).toBeVisible();
  const update = page.getByRole("button", { name: "Update", exact: true });
  await expect(update).toBeEnabled();
  await expect(update).toHaveCSS("opacity", "1");
  await expectAccessibleLayout(page);
  await keyboardActivate(
    page,
    page.getByRole("button", { name: "Review checkout", exact: true }),
  );
  await expect(
    page.getByRole("heading", { name: "Review your order" }),
  ).toBeVisible();
  await expectAccessibleLayout(page);
  await keyboardActivate(
    page,
    page.getByRole("button", { name: "Place demo order", exact: true }),
  );
  await expect(
    page.getByRole("heading", { name: "Your demo order" }),
  ).toBeVisible();
  const orderPath = new URL(page.url()).pathname;
  const orderId = Number(orderPath.split("/").at(-1));
  await expect(
    page
      .getByRole("main")
      .getByText("Awaiting sandbox payment", { exact: false }),
  ).toBeVisible();
  await expectAccessibleLayout(page);
  await page.route("https://checkout.stripe.com/**", (route) =>
    route.fulfill({
      contentType: "text/html",
      body: "<h1>Disposable sandbox provider</h1>",
    }),
  );
  await keyboardActivate(
    page,
    page.getByRole("button", { name: "Pay with Stripe sandbox", exact: true }),
  );
  await expect(
    page.getByRole("heading", { name: "Disposable sandbox provider" }),
  ).toBeVisible();
  expect(
    (
      await request.post(`${API}/__test/payment-event`, {
        data: {
          order_id: orderId,
          state: "paid",
          event_id: `evt_accessibility_${orderId}`,
        },
      })
    ).status(),
  ).toBe(200);
  await page.goto(`${orderPath}?payment=return`);
  await expect(
    page.getByRole("main").getByText("Paid — sandbox only", { exact: false }),
  ).toBeVisible();
  await expect(page.getByRole("main").getByRole("status")).toContainText(
    "Sandbox payment confirmed by the server",
  );
  await expectAccessibleLayout(page);
  await keyboardActivate(
    page,
    page.getByRole("link", { name: "Order history", exact: true }),
  );
  await expect(
    page.getByRole("link", { name: new RegExp(`Order #${orderId} — Paid`) }),
  ).toBeVisible();
  await expectAccessibleLayout(page);
});
