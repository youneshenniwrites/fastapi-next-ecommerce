import type { APIRequestContext } from "@playwright/test";
import { test, expect } from "./security-fixture";
import {
  expectAccessibleLayout,
  keyboardActivate,
} from "./accessibility-helpers";
test("empty catalog and upstream failure are distinct and recoverable", async ({
  page,
  request,
}) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await request.post("http://127.0.0.1:18301/scenario/empty");
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "A little space for something new." }),
  ).toBeVisible();
  await expectAccessibleLayout(page);
  await request.post("http://127.0.0.1:18301/scenario/error");
  await page.reload();
  await expect(
    page.getByRole("alert", { name: "Catalog unavailable" }),
  ).toContainText("We couldn’t reach the catalog");
  await request.post("http://127.0.0.1:18301/scenario/empty");
  await expectAccessibleLayout(page);
  await keyboardActivate(page, page.getByRole("button", { name: "Try again" }));
  await expect(
    page.getByRole("heading", { name: "A little space for something new." }),
  ).toBeVisible();
});
test("loading state is visible while catalog fetch is pending", async ({
  page,
  request,
}) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await request.post("http://127.0.0.1:18301/scenario/slow");
  await page.goto("/", { waitUntil: "commit" });
  await expect(
    page.getByRole("status", { name: "Loading collection" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Room to think. Space to create." }),
  ).toBeVisible();
  await expect(page.locator('[data-slot="skeleton"]').first()).toHaveCSS(
    "animation-name",
    "none",
  );
  await expectAccessibleLayout(page);
  await expect(
    page.getByRole("heading", { name: "A little space for something new." }),
  ).toBeVisible();
  await request.post("http://127.0.0.1:18301/scenario/empty");
});

const scenario = (request: APIRequestContext, mode: string) =>
  request.post(`http://127.0.0.1:18301/scenario/${mode}`);

test.describe("collection search states", () => {
  test.afterEach(async ({ request }) => {
    await scenario(request, "empty");
  });

  test("a slow search shows loading while the controls stay usable", async ({
    page,
    request,
  }) => {
    await scenario(request, "empty");
    await page.goto("/");
    const loading = page.getByRole("status", { name: "Loading collection" });
    await expect(
      page.getByRole("heading", { name: "A little space for something new." }),
    ).toBeVisible();
    await scenario(request, "slow");
    const search = page.getByRole("searchbox", { name: "Search collection" });
    const stock = page.getByRole("checkbox", { name: "In stock only" });
    await stock.click();
    await expect(loading).toBeVisible();
    await expect(stock).toBeChecked();
    await expect(search).toBeVisible();
    await expect(
      page.getByRole("combobox", { name: "Sort products" }),
    ).toBeVisible();
    await search.fill("lamp");
    await search.press("Enter");
    await expect(
      page.getByRole("button", { name: "Searching…" }),
    ).toBeDisabled();
    await expect(search).toHaveValue("lamp");
    await expect(loading).toBeVisible();
    await expect(page).toHaveURL(/\/\?q=lamp&in_stock=1#collection$/);
    await expect(
      page.getByRole("heading", { name: "No objects found." }),
    ).toBeVisible();
    await expect(loading).toHaveCount(0);
    await expect(search).toHaveValue("lamp");
    await expect(stock).toBeChecked();
  });

  test("a directly opened search link shows the loading skeleton", async ({
    page,
    request,
  }) => {
    await scenario(request, "slow");
    await page.goto("/?q=x", { waitUntil: "commit" });
    await expect(
      page.getByRole("status", { name: "Loading collection" }),
    ).toBeVisible();
    await expect(
      page.getByRole("searchbox", { name: "Search collection" }),
    ).toHaveValue("x");
    await expect(
      page.getByRole("heading", { name: "No objects found." }),
    ).toBeVisible();
  });

  test("a failed search can be retried", async ({ page, request }) => {
    await scenario(request, "error");
    await page.goto("/?q=x");
    await expect(
      page.getByRole("alert", { name: "Catalog unavailable" }),
    ).toBeVisible();
    await expect(
      page.getByRole("searchbox", { name: "Search collection" }),
    ).toHaveValue("x");
    await scenario(request, "empty");
    await page.getByRole("button", { name: "Try again" }).click();
    await expect(
      page.getByRole("heading", { name: "No objects found." }),
    ).toBeVisible();
    await expect(
      page.getByRole("alert", { name: "Catalog unavailable" }),
    ).toHaveCount(0);
  });

  test("a page beyond the current results recovers to the last page", async ({
    page,
    request,
  }) => {
    await scenario(request, "range");
    await page.setViewportSize({ width: 320, height: 740 });
    await page.goto("/?page=5");
    await expect(
      page.getByRole("heading", { name: "That page doesn’t exist." }),
    ).toBeVisible();
    await expect(
      page.locator("#collection").getByText("This selection has 2 pages."),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Go to the last page" }),
    ).toHaveAttribute("href", "/?page=2#collection");
    await expect(
      page.getByRole("link", { name: "Back to page one" }),
    ).toHaveAttribute("href", "/#collection");
    await expectAccessibleLayout(page);
  });
});
