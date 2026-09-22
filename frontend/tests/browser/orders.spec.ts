import AxeBuilder from "@axe-core/playwright";
import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:18300";

for (const scenario of [
  "normal",
  "lost response",
  "cart conflict",
  "stock conflict",
])
  test(`checkout places one owned order and shows confirmation/history (${scenario})`, async ({
    page,
    request,
  }) => {
    const email = `orders-${crypto.randomUUID()}@example.com`;
    const password = "disposable-order-password";
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
          headers: { Origin: "http://127.0.0.1:3300" },
          data: { email, password },
        })
      ).status(),
    ).toBe(200);
    await page.goto("/orders");
    await expect(
      page.getByRole("main").getByText("No orders on this page yet."),
    ).toBeVisible();
    const token = (await page.context().cookies()).find(
      (c) => c.name === "local-session",
    )!.value;
    const headers = { Authorization: `Bearer ${token}` };
    const products = await (
      await request.get(`${API}/api/v1/products/`)
    ).json();
    const product = products.find((p: { stock: number }) => p.stock > 0);
    const requestedQuantity = scenario === "stock conflict" ? product.stock : 1;
    expect(
      (
        await request.put(`${API}/api/v1/cart/items/${product.id}`, {
          headers,
          data: { quantity: requestedQuantity },
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
    const url = page.url();
    await expect(
      page
        .getByRole("main")
        .getByText(
          `Total: £${(Number(product.price) * requestedQuantity).toFixed(2)} GBP`,
          {
            exact: true,
          },
        ),
    ).toBeVisible();
    expect(
      (await new AxeBuilder({ page }).include("main").analyze()).violations,
    ).toEqual([]);
    if (scenario === "lost response") {
      await page.route("**/orders/*", async (route) => {
        if (route.request().method() !== "POST") return route.continue();
        await route.fetch(); // The mutation completes before its response is lost.
        await route.abort("failed");
      });
    }
    if (scenario === "cart conflict") {
      expect(
        (
          await request.delete(`${API}/api/v1/cart/items/${product.id}`, {
            headers,
          })
        ).status(),
      ).toBe(204);
    }
    if (scenario === "stock conflict") {
      const buyer = `competing-${crypto.randomUUID()}@example.com`;
      expect(
        (
          await request.post(`${API}/api/v1/auth/register`, {
            data: { email: buyer, password },
          })
        ).status(),
      ).toBe(201);
      const login = await request.post(`${API}/api/v1/auth/login`, {
        form: { username: buyer, password },
      });
      expect(login.status()).toBe(200);
      const competingHeaders = {
        Authorization: `Bearer ${(await login.json()).access_token}`,
      };
      expect(
        (
          await request.put(`${API}/api/v1/cart/items/${product.id}`, {
            headers: competingHeaders,
            data: { quantity: 1 },
          })
        ).status(),
      ).toBe(200);
      const draft = await request.post(`${API}/api/v1/orders/drafts`, {
        headers: competingHeaders,
        data: { lines: [{ product_id: product.id, quantity: 1 }] },
      });
      expect(draft.status()).toBe(201);
      const competitorId = (await draft.json()).id;
      expect(
        (
          await request.post(`${API}/api/v1/orders/${competitorId}/place`, {
            headers: {
              ...competingHeaders,
              "Idempotency-Key": `competitor-${competitorId}`,
            },
          })
        ).status(),
      ).toBe(200);
    }
    const place = page.getByRole("button", { name: "Place demo order" });
    if (scenario === "normal") {
      // The first click can refocus a window and start session verification.
      const box = (await place.boundingBox())!;
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await page.mouse.down();
      await page.evaluate(() => window.dispatchEvent(new Event("focus")));
      await page.mouse.up();
    } else {
      await place.focus();
      await page.keyboard.press("Enter");
    }
    if (scenario === "stock conflict") {
      await expect(page.getByRole("main").getByRole("alert")).toContainText(
        "stock changed",
      );
      await page.getByRole("link", { name: "Your cart", exact: true }).click();
      await expect(
        page.getByText("Limited stock", { exact: true }),
      ).toBeVisible();
      await page
        .getByRole("button", { name: "Review checkout", exact: true })
        .click();
      await expect(page.getByRole("main").getByRole("alert")).toContainText(
        "no longer available",
      );
      const drafts = await (
        await request.get(`${API}/api/v1/orders/`, { headers })
      ).json();
      expect(drafts).toHaveLength(1);
      expect(drafts[0].status).toBe("draft");
      return;
    }
    if (scenario === "lost response") {
      await expect(page.getByRole("main").getByRole("alert")).toContainText(
        "lost the response",
      );
      await page.unroute("**/orders/*");
      await page.getByRole("button", { name: "Place demo order" }).click();
    }
    if (scenario === "cart conflict") {
      await expect(page.getByRole("main").getByRole("alert")).toContainText(
        "stock changed",
      );
      expect(
        (
          await request.put(`${API}/api/v1/cart/items/${product.id}`, {
            headers,
            data: { quantity: 1 },
          })
        ).status(),
      ).toBe(200);
      await page.getByRole("button", { name: "Place demo order" }).click();
    }
    await expect(
      page.getByRole("heading", { name: "Order confirmed" }),
    ).toBeVisible();
    await expect(
      page.getByRole("main").getByText("Placed — unpaid", { exact: false }),
    ).toBeVisible();
    await page.reload();
    await expect(
      page.getByRole("heading", { name: "Order confirmed" }),
    ).toBeVisible();
    const id = Number(url.split("/").at(-1));
    const replay = await request.post(`${API}/api/v1/orders/${id}/place`, {
      headers: { ...headers, "Idempotency-Key": `storefront-order-${id}` },
    });
    expect(replay.status()).toBe(200);
    const orders = await (
      await request.get(`${API}/api/v1/orders/`, { headers })
    ).json();
    expect(
      orders.filter((order: { status: string }) => order.status === "placed"),
    ).toHaveLength(1);
    await page
      .getByRole("link", { name: "Order history", exact: true })
      .click();
    await expect(
      page.getByRole("link", { name: new RegExp(`Order #${id} — Placed`) }),
    ).toBeVisible();
    await page.context().clearCookies();
    await page.goto(url);
    await expect(
      page.getByRole("main").getByText("Sign in to view your order."),
    ).toBeVisible();
    await expect(
      page.getByRole("main").getByText(product.name, { exact: true }),
    ).toHaveCount(0);
  });
