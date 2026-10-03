import { test, expect } from "./security-fixture";
import AxeBuilder from "@axe-core/playwright";

test("baseline security headers cover pages, errors and assets", async ({
  page,
  request,
}) => {
  for (const [path, status] of [
    ["/", 200],
    ["/login", 200],
    ["/not-a-route", 404],
    ["/api/session/me", 401],
  ] as const) {
    const response = await request.get(path);
    expect(response.status()).toBe(status);
    expect(response.headers()["x-content-type-options"]).toBe("nosniff");
    expect(response.headers()["referrer-policy"]).toBe(
      "strict-origin-when-cross-origin",
    );
    expect(response.headers()["content-type"]).toContain(
      path === "/api/session/me" ? "application/json" : "text/html",
    );
    if (path === "/api/session/me") {
      expect(response.headers()["cache-control"]).toBe("private, no-store");
    }
  }
  for (const [path, destination] of [
    ["/login/?next=%2Fcart", "/login?next=%2Fcart"],
    ["/products/1/", "/products/1"],
    ["/api/session/me/", "/api/session/me"],
  ]) {
    const redirect = await request.get(path, { maxRedirects: 0 });
    expect(redirect.status()).toBe(308);
    expect(redirect.headers()["location"]).toBe(destination);
    // Next's framework normalization precedes configured headers. Preserve
    // its canonical URL/query behavior; this empty 308 is an explicit exception.
  }
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("12 objects");
  const script = await page
    .locator('script[src^="/_next/static/"]')
    .first()
    .getAttribute("src");
  const style = await page
    .locator('link[rel="stylesheet"]')
    .first()
    .getAttribute("href");
  expect(script).toBeTruthy();
  expect(style).toBeTruthy();
  for (const [path, type] of [
    [script!, "javascript"],
    [style!, "text/css"],
  ]) {
    const response = await request.get(path);
    expect(response.status()).toBe(200);
    expect(response.headers()["content-type"]).toContain(type);
    expect(response.headers()["cache-control"]).toContain("immutable");
    expect(response.headers()["x-content-type-options"]).toBe("nosniff");
    expect(response.headers()["referrer-policy"]).toBe(
      "strict-origin-when-cross-origin",
    );
  }
});

test("enforced CSP uses fresh nonces on real pages and preserves hydration", async ({
  page,
  request,
}) => {
  let previous = "";
  for (const path of [
    "/",
    "/login",
    "/register",
    "/not-a-route",
    "/sentry-tunnel-extra",
    "/_next/image-extra",
    "/favicon.ico-extra",
    "/api/not-a-route",
    "/photos/not-a-photo",
  ]) {
    const response = await page.goto(path);
    const headers = response!.headers();
    const candidate = headers["content-security-policy"];
    expect(headers["content-security-policy-report-only"]).toBeUndefined();
    expect(headers["x-frame-options"]).toBe("DENY");
    expect(headers["cache-control"]).toContain("private");
    expect(headers["cache-control"]).toContain("no-store");
    const nonce = candidate.match(/'nonce-([^']+)'/)![1];
    expect(nonce).not.toBe(previous);
    previous = nonce;
    const scripts = await page
      .locator("script:not([src])")
      .evaluateAll((nodes) =>
        nodes.map((node) => (node as HTMLScriptElement).nonce),
      );
    expect(scripts.length).toBeGreaterThan(0);
    expect(scripts.every((value) => value === nonce)).toBe(true);
  }
  const photo = await request.get("/photos/mat.webp");
  expect(photo.status()).toBe(200);
  expect(photo.headers()["content-type"]).toContain("image/webp");
  expect(photo.headers()["cache-control"]).not.toContain("private");
  expect(photo.headers()["cache-control"]).not.toContain("no-store");
  const forged = await request.get("/login", {
    headers: {
      "x-nonce": "attacker",
      "x-vindor-render-csp": "script-src 'nonce-attacker'",
      "content-security-policy": "script-src 'nonce-attacker'",
      "content-security-policy-report-only": "script-src 'unsafe-inline'",
    },
  });
  const policy = forged.headers()["content-security-policy"];
  expect(policy).not.toContain("attacker");
  expect(policy).toContain("'strict-dynamic'");
});

// A tap can land mid-remount and be swallowed, so re-try until the menu is visible
// instead of failing outright.
async function openMobileMenu(page: import("@playwright/test").Page) {
  const dialog = page.getByRole("dialog", { name: "Explore VINDOR" });
  for (let attempt = 0; attempt < 3; attempt++) {
    await page.getByRole("button", { name: "Open navigation" }).click();
    const opened = await dialog
      .waitFor({ state: "visible", timeout: 3000 })
      .then(
        () => true,
        () => false,
      );
    if (opened) return;
  }
  await expect(dialog).toBeVisible();
}
test("browse, filter and view the real FastAPI catalog", async ({
  page,
}, info) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Room to think. Space to create." }),
  ).toBeVisible();
  await expect(page.getByRole("status")).toHaveText("12 objects");
  await page.getByRole("searchbox").fill("not present");
  await expect(
    page.getByRole("heading", { name: "No objects found." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Clear filters" }).click();
  await page.getByRole("checkbox", { name: "In stock only" }).check();
  await expect(page.getByRole("status")).toHaveText("11 objects");
  await page.getByRole("combobox", { name: "Sort products" }).click();
  await page
    .getByRole("option", { name: "Price: low to high", exact: true })
    .click();
  await expect(page.locator(".product h3").first()).toHaveText("Notebook Set");
  await page.getByRole("searchbox").fill("Oak");
  await page.getByRole("link", { name: /Oak Monitor Stand/ }).click();
  await expect(
    page.getByRole("heading", { name: "Oak Monitor Stand", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".detail-price")).toContainText("£79.00");
  await expect(page.getByText("In stock", { exact: true })).toBeVisible();
  await expect(
    page.getByText(
      /Demo orders can be placed at checkout\. Payments, when enabled, use a sandbox; no real money is charged\./,
    ),
  ).toBeVisible();
  await page.screenshot({
    path: `test-results/detail-${info.project.name}.png`,
    fullPage: true,
  });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});
test("out-of-stock, missing products and responsive keyboard navigation", async ({
  page,
}, info) => {
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("12 objects");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to content" }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect
    .poll(() => page.evaluate(() => document.documentElement.scrollWidth))
    .toBeLessThanOrEqual(page.viewportSize()!.width);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: `test-results/catalog-${info.project.name}.png`,
    fullPage: true,
  });
  await page.getByRole("link", { name: /Ceramic Pen Cup/ }).click();
  await expect(page.getByText("Out of stock", { exact: true })).toBeVisible();
  await page.goto("/products/999999");
  await expect(
    page.getByRole("heading", { name: "This object has moved on." }),
  ).toBeVisible();
  await page.goto("/products/not-an-id");
  await expect(
    page.getByRole("heading", { name: "This object has moved on." }),
  ).toBeVisible();
});

test("shared action and stock badge use the VINDOR theme", async ({ page }) => {
  await page.goto("/");
  const action = page.getByRole("link", { name: /Explore the collection/ });
  await expect(action).toHaveCSS("background-color", "rgb(48, 78, 60)");
  await expect(action).toHaveCSS("color", "rgb(255, 255, 255)");
  await expect(action).toHaveCSS("border-radius", "4px");
  // Role locators exclude the hidden Suspense copy of the filter bar, so hydration
  // cannot fail these assertions with strict-mode violations.
  const search = page.getByRole("searchbox", { name: "Search collection" });
  const sort = page.getByRole("combobox", { name: "Sort products" });
  await expect(search).toHaveCSS("border-radius", "4px");
  await expect(sort).toHaveCSS("border-radius", "4px");
  await search.fill("Oak");
  await expect(page.getByRole("status")).toHaveText("1 object");
  await search.focus();
  await expect(search).toBeFocused();
  await expect(search).toHaveCSS("box-shadow", "none");
  await expect(search).toHaveCSS("outline-width", "2px");
  await action.focus();
  await expect(action).toBeFocused();
  await expect(action).toHaveCSS("outline-style", "solid");
  await search.fill("");
  await expect(
    page.getByRole("main").locator('[data-slot="badge"]'),
  ).toHaveText("Out of stock");
});

test("mobile navigation supports keyboard, dismissal and real links", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "mobile", "Mobile menu only");
  await page.goto("/");
  await page.emulateMedia({ reducedMotion: "reduce" });
  const trigger = page.getByRole("button", { name: "Open navigation" });
  const dialog = page.getByRole("dialog", { name: "Explore VINDOR" });
  for (let attempt = 0; attempt < 3; attempt++) {
    // Re-focus every attempt: opening the menu moves focus, and a
    // background refresh can drop it back to the document.
    await trigger.focus();
    await page.keyboard.press("Enter");
    const opened = await dialog
      .waitFor({ state: "visible", timeout: 3000 })
      .then(
        () => true,
        () => false,
      );
    if (opened) break;
  }
  await expect(dialog).toBeVisible();
  await page.screenshot({
    path: "test-results/mobile-menu.png",
    fullPage: true,
  });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(trigger).toBeFocused();
  await openMobileMenu(page);
  await page
    .getByRole("navigation", { name: "Mobile navigation" })
    .getByRole("link", { name: "The collection" })
    .click();
  await expect(dialog).not.toBeVisible();
  await expect(page).toHaveURL(/#collection$/);
  await page.setViewportSize({ width: 320, height: 740 });
  // innerWidth grows to match overflowing content on mobile; the configured
  // viewport remains 320px and catches clipped product actions.
  await expect
    .poll(() => page.evaluate(() => document.documentElement.scrollWidth))
    .toBeLessThanOrEqual(page.viewportSize()!.width);
});

test("mobile navigation closes when resizing to desktop", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "mobile", "Mobile menu only");
  await page.goto("/");
  await page.emulateMedia({ reducedMotion: "reduce" });
  const trigger = page.getByRole("button", { name: "Open navigation" });
  const dialog = page.getByRole("dialog", { name: "Explore VINDOR" });
  await openMobileMenu(page);
  await expect(dialog).toBeVisible();
  await page.setViewportSize({ width: 1280, height: 900 });
  await expect(dialog).not.toBeVisible();
  await expect(page.locator('[data-slot="sheet-overlay"]')).toHaveCount(0);
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("link", { name: "Our approach" })
    .click();
  await expect(page).toHaveURL(/#approach$/);
  await page.setViewportSize({ width: 393, height: 851 });
  await expect(dialog).not.toBeVisible();
  await openMobileMenu(page);
  await expect(dialog).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(trigger).toBeFocused();
});

test("VINDOR branding and local photographs load", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle("VINDOR — Room to think");
  await expect(page.getByRole("link", { name: "VINDOR home" })).toHaveCount(2);
  await expect(page.getByRole("status")).toHaveText("12 objects");
  const photos = page.getByRole("main").locator("img");
  await expect(photos).toHaveCount(13);
  for (const photo of await photos.all()) {
    await photo.scrollIntoViewIfNeeded();
    await expect
      .poll(() =>
        photo.evaluate((img) => (img as HTMLImageElement).naturalWidth),
      )
      .toBeGreaterThan(0);
    await expect(photo).toHaveAttribute("src", /photos/);
    await expect(photo).not.toHaveAttribute("src", /\.svg/);
  }
  await expect(page.getByRole("link", { name: "Photo credits" })).toBeVisible();
});

test("new products have distinct photographs and working detail pages", async ({
  page,
}) => {
  await page.goto("/");
  const sources = await page
    .locator(".product img")
    .evaluateAll((images) => images.map((image) => image.getAttribute("src")));
  expect(new Set(sources).size).toBe(12);
  for (const name of [
    "Compact Keyboard",
    "Focus Headphones",
    "Insulated Bottle",
    "Handled Planter",
    "Analogue Desk Clock",
    "Wireless Mouse",
  ]) {
    await page.goto("/");
    await page.getByRole("searchbox").fill(name);
    await expect(page.getByRole("status")).toHaveText("1 object");
    await page.getByRole("link", { name: new RegExp(name) }).click();
    await expect(
      page.getByRole("heading", { name, exact: true }),
    ).toBeVisible();
    await expect(page.locator(".detail-price")).toContainText("£");
    await expect(page.getByRole("main").getByText(/Fictional/)).toBeVisible();
    const photo = page.getByRole("main").locator("img");
    await expect
      .poll(() =>
        photo.evaluate((image) => (image as HTMLImageElement).naturalWidth),
      )
      .toBeGreaterThan(0);
  }
});

test.describe("CSP negative probes", () => {
  test.use({ allowCspViolations: true });
  test("enforced CSP blocks untrusted inline scripts", async ({
    page,
    cspViolations,
  }) => {
    await page.route("**/login", async (route) => {
      const response = await route.fetch();
      const body = (await response.text()).replace(
        "</body>",
        "<script>window.fictionalInlineProbe = true</script></body>",
      );
      await route.fulfill({ response, body });
    });
    await page.goto("/login");
    expect(
      await page.evaluate(() => Reflect.get(window, "fictionalInlineProbe")),
    ).toBeUndefined();
    await expect
      .poll(() =>
        cspViolations.some(
          (v) =>
            v.disposition === "enforce" && v.directive.startsWith("script-src"),
        ),
      )
      .toBe(true);
  });

  test("a neutral cross-origin parent cannot frame the storefront", async ({
    page,
  }) => {
    const denied: string[] = [];
    const browserLog = await page.context().newCDPSession(page);
    await browserLog.send("Log.enable");
    browserLog.on("Log.entryAdded", ({ entry }) => {
      if (
        /frame-ancestors|X-Frame-Options/i.test(entry.text) &&
        !/report-only/i.test(entry.text)
      )
        denied.push("framing denied");
    });
    await page.goto("http://127.0.0.1:18301/frame-probe");
    await expect.poll(() => denied.includes("framing denied")).toBe(true);
    await expect
      .poll(() =>
        page.frames().some((frame) => frame.url().startsWith("chrome-error:")),
      )
      .toBe(true);
  });
});

test("API documentation renders under its enforced policies", async ({
  page,
  isMobile,
}) => {
  await page.goto("http://127.0.0.1:18300/docs");
  await expect(page.locator(".swagger-ui .info .title")).toContainText(
    "E-Commerce API",
  );
  await page.locator("#operations-Health-health_check_health_get").click();
  await page.getByRole("button", { name: "Try it out" }).click();
  const healthResponse = page.waitForResponse(
    (response) =>
      response.url() === "http://127.0.0.1:18300/health" &&
      response.request().method() === "GET",
  );
  await page.getByRole("button", { name: "Execute", exact: true }).click();
  const health = await healthResponse;
  expect(health.status()).toBe(200);
  expect(await health.json()).toEqual({ status: "ok" });
  await page.goto("http://127.0.0.1:18300/redoc");
  await expect(
    page.getByRole("heading", { name: "E-Commerce API" }),
  ).toBeVisible();
  // ReDoc's pinned mobile navigation toggle is the sidebar's adjacent sibling.
  if (isMobile) await page.locator(".menu-content + div").click();
  const results = page.locator('[data-role="search:results"]');
  await expect(results).toHaveCount(0);
  await page
    .getByRole("textbox", { name: "Search", exact: true })
    .fill("health");
  await expect(
    results.getByRole("menuitem", {
      name: "Check API process liveness",
      exact: true,
    }),
  ).toBeVisible();
});
