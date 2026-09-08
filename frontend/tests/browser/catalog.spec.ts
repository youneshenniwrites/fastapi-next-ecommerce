import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
test("browse, filter and view the real FastAPI catalog", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Room to think. Space to create." }),
  ).toBeVisible();
  await expect(page.getByRole("status")).toHaveText("6 objects");
  await page.getByRole("searchbox").fill("not present");
  await expect(
    page.getByRole("heading", { name: "No objects found." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Clear filters" }).click();
  await page.getByLabel("In stock only").check();
  await expect(page.getByRole("status")).toHaveText("5 objects");
  await page.getByLabel("Sort products").selectOption("price-asc");
  await expect(page.locator(".product h3").first()).toHaveText("Notebook Set");
  await page.getByRole("searchbox").fill("Oak");
  await page.getByRole("link", { name: /Oak Monitor Stand/ }).click();
  await expect(
    page.getByRole("heading", { name: "Oak Monitor Stand", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".detail-price")).toContainText("£79.00");
  await expect(page.getByText("In stock", { exact: true })).toBeVisible();
  await expect(page.getByText(/no purchases can be made/)).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});
test("out-of-stock, missing products and responsive keyboard navigation", async ({
  page,
}, info) => {
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("6 objects");
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
