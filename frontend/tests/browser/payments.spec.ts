import AxeBuilder from "@axe-core/playwright";
import { test, expect } from "@playwright/test";

const API = "http://127.0.0.1:18302";
const ORIGIN = "http://127.0.0.1:3302";

for (const outcome of [
  "paid",
  "cancelled",
  "expired",
  "failed",
  "lost response",
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
      const state = outcome === "lost response" ? "paid" : outcome;
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
      outcome === "paid" || outcome === "lost response"
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
