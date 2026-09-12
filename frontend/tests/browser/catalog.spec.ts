import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
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
  await page.getByLabel("In stock only").check();
  await expect(page.getByRole("status")).toHaveText("11 objects");
  await page.getByLabel("Sort products").click();
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
  await expect(page.getByText(/no purchases can be made/)).toBeVisible();
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
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
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
  await expect(page.getByLabel("Search collection")).toHaveCSS(
    "border-radius",
    "4px",
  );
  await expect(page.getByLabel("Sort products")).toHaveCSS(
    "border-radius",
    "4px",
  );
  await page.getByLabel("Search collection").fill("Oak");
  await expect(page.getByRole("status")).toHaveText("1 object");
  await page.getByLabel("Search collection").focus();
  await expect(page.getByLabel("Search collection")).toBeFocused();
  await expect(page.getByLabel("Search collection")).toHaveCSS(
    "box-shadow",
    "none",
  );
  await expect(page.getByLabel("Search collection")).toHaveCSS(
    "outline-width",
    "2px",
  );
  await action.focus();
  await expect(action).toBeFocused();
  await expect(action).toHaveCSS("outline-style", "solid");
  await page.getByLabel("Search collection").fill("");
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
  await trigger.focus();
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog", { name: "Explore VINDOR" });
  await expect(dialog).toBeVisible();
  await page.screenshot({
    path: "test-results/mobile-menu.png",
    fullPage: true,
  });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(trigger).toBeFocused();
  await trigger.click();
  await page
    .getByRole("navigation", { name: "Mobile navigation" })
    .getByRole("link", { name: "The collection" })
    .click();
  await expect(dialog).not.toBeVisible();
  await expect(page).toHaveURL(/#collection$/);
  await page.setViewportSize({ width: 320, height: 740 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
});

test("mobile navigation closes when resizing to desktop", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "mobile", "Mobile menu only");
  await page.goto("/");
  await page.emulateMedia({ reducedMotion: "reduce" });
  const trigger = page.getByRole("button", { name: "Open navigation" });
  const dialog = page.getByRole("dialog", { name: "Explore VINDOR" });
  await trigger.click();
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
  await trigger.click();
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
