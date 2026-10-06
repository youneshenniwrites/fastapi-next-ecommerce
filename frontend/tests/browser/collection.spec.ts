import { test, expect } from "./security-fixture";
import type { Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { expectAccessibleLayout } from "./accessibility-helpers";

// The fixture catalog has 60 products: 12 demo products plus 48 generated ones.
const total = 60;
const sorts = ["featured", "name", "price-asc", "price-desc"] as const;
const notice = "Some options in that link weren’t recognised";

const status = (page: Page) =>
  page.locator("#collection").getByRole("status").first();
const cards = (page: Page) => page.locator("#collection article.product h3");
const names = (page: Page) => cards(page).allTextContents();
const search = (page: Page) =>
  page.getByRole("searchbox", { name: "Search collection" });
const stock = (page: Page) =>
  page.getByRole("checkbox", { name: "In stock only" });
const sortBox = (page: Page) =>
  page.getByRole("combobox", { name: "Sort products" });
const pages = (page: Page) =>
  page.getByRole("navigation", { name: "Collection pages" });
const relative = (page: Page) => {
  const url = new URL(page.url());
  return `${url.pathname}${url.search}`;
};

async function chooseSort(page: Page, label: string) {
  await sortBox(page).click();
  await page.getByRole("option", { name: label, exact: true }).click();
}

async function ready(page: Page, text: string) {
  await expect(status(page)).toHaveText(text);
}

test("first page shows 24 objects with numbered, previous and next navigation", async ({
  page,
}) => {
  await page.goto("/");
  await ready(page, `${total} objects · Page 1 of 3`);
  await expect(cards(page)).toHaveCount(24);
  await expect(
    page.locator("#collection").getByText("Showing 1–24"),
  ).toBeVisible();
  await expect(
    pages(page).getByRole("link", { name: "Page 1" }),
  ).toHaveAttribute("aria-current", "page");
  await expect(pages(page).getByText("Previous")).toHaveAttribute(
    "aria-disabled",
    "true",
  );
  await expect(pages(page).getByRole("link", { name: "Previous" })).toHaveCount(
    0,
  );

  await pages(page).getByRole("link", { name: "Next" }).click();
  await ready(page, `${total} objects · Page 2 of 3`);
  expect(relative(page)).toBe("/?page=2");
  await expect(cards(page)).toHaveCount(24);
  await expect(
    page.locator("#collection").getByText("Showing 25–48"),
  ).toBeVisible();

  await pages(page).getByRole("link", { name: "Page 3" }).click();
  await ready(page, `${total} objects · Page 3 of 3`);
  await expect(cards(page)).toHaveCount(12);
  await expect(
    page.locator("#collection").getByText("Showing 49–60"),
  ).toBeVisible();
  await expect(pages(page).getByRole("link", { name: "Next" })).toHaveCount(0);

  await pages(page).getByRole("link", { name: "Previous" }).click();
  await ready(page, `${total} objects · Page 2 of 3`);
  await pages(page).getByRole("link", { name: "Page 1" }).click();
  await ready(page, `${total} objects · Page 1 of 3`);
  expect(relative(page)).toBe("/");
});

test("direct load, refresh, Back and Forward reproduce controls and results", async ({
  page,
}) => {
  const url = "/?q=Studio&in_stock=1&sort=price-desc&page=2";
  await page.goto(url);
  await ready(page, "30 objects · Page 2 of 2");
  const second = await names(page);
  expect(second).toHaveLength(6);
  await expect(search(page)).toHaveValue("Studio");
  await expect(stock(page)).toBeChecked();
  await expect(sortBox(page)).toHaveText("Price: high to low");

  await page.reload();
  await ready(page, "30 objects · Page 2 of 2");
  expect(await names(page)).toEqual(second);

  await pages(page).getByRole("link", { name: "Page 1" }).click();
  await ready(page, "30 objects · Page 1 of 2");
  const first = await names(page);
  expect(first).toHaveLength(24);

  await page.goBack();
  await ready(page, "30 objects · Page 2 of 2");
  expect(await names(page)).toEqual(second);
  await expect(search(page)).toHaveValue("Studio");

  await search(page).fill("Lumen");
  await search(page).press("Enter");
  await ready(page, "8 objects");
  await page.goBack();
  await ready(page, "30 objects · Page 2 of 2");
  await expect(search(page)).toHaveValue("Studio");
  await page.goForward();
  await ready(page, "8 objects");
  await expect(search(page)).toHaveValue("Lumen");
  await expect(stock(page)).toBeChecked();
  await expect(sortBox(page)).toHaveText("Price: high to low");
});

for (const sort of sorts) {
  test(`every product appears exactly once across pages (${sort})`, async ({
    page,
  }) => {
    const seen: string[] = [];
    for (const number of [1, 2, 3]) {
      await page.goto(`/?sort=${sort}&page=${number}`);
      await ready(page, `${total} objects · Page ${number} of 3`);
      seen.push(...(await names(page)));
    }
    expect(seen).toHaveLength(total);
    expect(new Set(seen).size).toBe(total);
  });
}

test("search needs an explicit submit and combines with stock and sort", async ({
  page,
}) => {
  await page.goto("/");
  await ready(page, `${total} objects · Page 1 of 3`);
  await search(page).pressSequentially("Studio", { delay: 20 });
  await expect(search(page)).toHaveValue("Studio");
  expect(relative(page)).toBe("/");
  await expect(status(page)).toHaveText(`${total} objects · Page 1 of 3`);

  await page.getByRole("button", { name: "Search", exact: true }).click();
  await ready(page, "34 objects · Page 1 of 2");
  expect(relative(page)).toBe("/?q=Studio");

  await stock(page).click();
  await ready(page, "30 objects · Page 1 of 2");
  expect(relative(page)).toBe("/?q=Studio&in_stock=1");
  await chooseSort(page, "Price: low to high");
  await ready(page, "30 objects · Page 1 of 2");
  expect(relative(page)).toBe("/?q=Studio&in_stock=1&sort=price-asc");
  const prices = await page
    .locator("#collection article.product span.whitespace-nowrap")
    .allTextContents();
  const values = prices.map((price) => Number(price.replace(/[^\d.]/g, "")));
  expect(values).toEqual([...values].sort((a, b) => a - b));
  expect((await names(page)).every((name) => name.includes("Studio"))).toBe(
    true,
  );

  await page.getByRole("link", { name: "Clear all filters" }).click();
  await ready(page, `${total} objects · Page 1 of 3`);
  expect(relative(page)).toBe("/");
  await expect(search(page)).toHaveValue("");
  await expect(stock(page)).not.toBeChecked();
});

test("changing any filter from page 3 returns to page 1", async ({ page }) => {
  await page.goto("/?page=3");
  await ready(page, `${total} objects · Page 3 of 3`);
  await stock(page).click();
  await ready(page, "51 objects · Page 1 of 3");
  expect(relative(page)).toBe("/?in_stock=1");

  await page.goto("/?page=3");
  await ready(page, `${total} objects · Page 3 of 3`);
  await chooseSort(page, "Name");
  await ready(page, `${total} objects · Page 1 of 3`);
  expect(relative(page)).toBe("/?sort=name");

  await page.goto("/?page=3");
  await ready(page, `${total} objects · Page 3 of 3`);
  await search(page).fill("Studio");
  await search(page).press("Enter");
  await ready(page, "34 objects · Page 1 of 2");
  expect(relative(page)).toBe("/?q=Studio");
});

test("percent and underscore search literally", async ({ page }) => {
  await page.goto("/");
  await search(page).fill("100%");
  await search(page).press("Enter");
  await ready(page, "1 object");
  await expect(cards(page)).toHaveText(["100% Wool Tray"]);
  expect(relative(page)).toBe("/?q=100%25");

  await search(page).fill("Under_score");
  await search(page).press("Enter");
  await ready(page, "1 object");
  await expect(cards(page)).toHaveText(["Under_score Stand"]);
  expect(relative(page)).toBe("/?q=Under_score");

  await page.goto("/?q=%25");
  await ready(page, "1 object");
  await page.goto("/?q=Studio_Item");
  await expect(
    page.getByRole("heading", { name: "No objects found." }),
  ).toBeVisible();
});

test("product pages return to the exact selection", async ({
  page,
  context,
}) => {
  await page.goto("/?q=Studio&in_stock=1&sort=name&page=2&utm_source=ad");
  await ready(page, "30 objects · Page 2 of 2");
  const first = (await names(page))[0];
  const card = page.getByRole("link", { name: new RegExp(first) }).first();
  const href = await card.getAttribute("href");
  expect(href).toMatch(
    /^\/products\/\d+\?q=Studio&in_stock=1&sort=name&page=2$/,
  );
  await card.click();
  await expect(
    page.getByRole("heading", { name: first, exact: true }),
  ).toBeVisible();
  const back = page.getByRole("link", { name: "Back to the collection" });
  await expect(back).toHaveAttribute(
    "href",
    "/?q=Studio&in_stock=1&sort=name&page=2#collection",
  );

  await page.reload();
  await expect(back).toHaveAttribute(
    "href",
    "/?q=Studio&in_stock=1&sort=name&page=2#collection",
  );

  const fresh = await context.newPage();
  await fresh.goto(href!);
  await expect(
    fresh.getByRole("link", { name: "Back to the collection" }),
  ).toHaveAttribute(
    "href",
    "/?q=Studio&in_stock=1&sort=name&page=2#collection",
  );
  await fresh.getByRole("link", { name: "Back to the collection" }).click();
  await expect(status(fresh)).toHaveText("30 objects · Page 2 of 2");
  await expect(search(fresh)).toHaveValue("Studio");
  await expect(stock(fresh)).toBeChecked();
  await expect(sortBox(fresh)).toHaveText("Name");
  expect(await names(fresh)).toContain(first);
  await fresh.close();

  await back.click();
  await ready(page, "30 objects · Page 2 of 2");
  await expect(search(page)).toHaveValue("Studio");
  await expect(stock(page)).toBeChecked();
  await expect(sortBox(page)).toHaveText("Name");
  expect(relative(page)).toBe("/?q=Studio&in_stock=1&sort=name&page=2");
});

test("product return links never follow external or unrecognised values", async ({
  page,
}) => {
  await page.goto(
    "/products/1?return=https://evil.example/&q=Oak&redirect=//evil.example&page=zzz",
  );
  const back = page.getByRole("link", { name: "Back to the collection" });
  await expect(back).toHaveAttribute("href", "/?q=Oak#collection");
  await page.goto("/products/1?q=a&q=b&sort=bogus");
  await expect(back).toHaveAttribute("href", "/#collection");
  for (const link of await page.locator("main a").all()) {
    expect(await link.getAttribute("href")).not.toContain("evil");
  }
});

test("invalid links fall back to the default view with a note", async ({
  page,
}) => {
  const long = "x".repeat(101);
  const links = [
    "/?page=abc",
    "/?page=0",
    "/?page=99999",
    "/?sort=bogus",
    "/?in_stock=yes",
    "/?q=a&q=b",
    `/?q=${long}`,
  ];
  for (const link of links) {
    await page.goto(link);
    await ready(page, `${total} objects · Page 1 of 3`);
    await expect(page.getByText(notice, { exact: false }), link).toBeVisible();
    await expect(search(page)).toHaveValue("");
    await expect(stock(page)).not.toBeChecked();
    await expect(sortBox(page)).toHaveText("Featured");
    expect(
      await page.locator("a[href*='evil']").count(),
      `${link} external link`,
    ).toBe(0);
  }
  await page.goto("/?q=Oak&unknown=1");
  await ready(page, "1 object");
  await expect(page.getByText(notice, { exact: false })).toHaveCount(0);
  await page.goto("/?return=https://evil.example&q=Oak");
  await expect(page.getByText(notice, { exact: false })).toHaveCount(0);
  await expect(page.locator("a[href*='evil']")).toHaveCount(0);
  await ready(page, "1 object");
  await page.goto("/?return=https://evil.example");
  await ready(page, `${total} objects · Page 1 of 3`);
  await expect(page.locator("a[href*='evil']")).toHaveCount(0);
});

test("out-of-range pages explain and recover", async ({ page }) => {
  await page.goto("/?page=9");
  await expect(
    page.getByRole("heading", { name: "That page doesn’t exist." }),
  ).toBeVisible();
  await expect(
    page.locator("#collection").getByText("This selection has 3 pages."),
  ).toBeVisible();
  await expect(cards(page)).toHaveCount(0);
  await page.getByRole("link", { name: "Go to the last page" }).click();
  await ready(page, `${total} objects · Page 3 of 3`);
  expect(relative(page)).toBe("/?page=3");
  await expect(cards(page)).toHaveCount(12);

  await page.goto("/?q=Studio&page=9");
  await page.getByRole("link", { name: "Back to page one" }).click();
  await ready(page, "34 objects · Page 1 of 2");
  expect(relative(page)).toBe("/?q=Studio");
});

test("no results offer a way back", async ({ page }) => {
  await page.goto("/?q=nothing-like-this&in_stock=1");
  await expect(
    page.getByRole("heading", { name: "No objects found." }),
  ).toBeVisible();
  await expect(status(page)).toHaveText("0 objects");
  await page.getByRole("link", { name: "Clear filters", exact: true }).click();
  await ready(page, `${total} objects · Page 1 of 3`);
});

async function replaceClipboard(page: Page, mode: "reject" | "deferred") {
  await page.evaluate((how) => {
    const win = window as unknown as {
      resolveCopy?: () => void;
      copied?: string;
    };
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: (text: string) => {
          if (how === "reject")
            return Promise.reject(
              new DOMException("denied", "NotAllowedError"),
            );
          win.copied = text;
          return new Promise<void>((resolve) => {
            win.resolveCopy = resolve;
          });
        },
      },
    });
  }, mode);
}

test("share copies the canonical recognised URL", async ({
  page,
  context,
  baseURL,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"], {
    origin: baseURL,
  });
  await page.goto(
    "/?utm_source=ad&page=2&sort=name&in_stock=1&q=Studio&return=https://evil.example",
  );
  await ready(page, "30 objects · Page 2 of 2");
  await page.getByRole("button", { name: "Share results" }).click();
  await expect(page.getByText("Collection link copied.")).toBeVisible();
  const copied = await page.evaluate(() => navigator.clipboard.readText());
  expect(copied).toBe(
    `${new URL(baseURL!).origin}/?q=Studio&in_stock=1&sort=name&page=2#collection`,
  );
  await expect(
    page.getByRole("textbox", { name: "Collection link" }),
  ).toHaveCount(0);
});

test("share falls back to a selectable link when copying fails", async ({
  page,
  baseURL,
}) => {
  await page.goto("/?q=Lumen");
  await ready(page, "12 objects");
  await replaceClipboard(page, "reject");
  await page.getByRole("button", { name: "Share results" }).click();
  await expect(page.getByText("Couldn’t copy automatically")).toBeVisible();
  const link = page.getByRole("textbox", { name: "Collection link" });
  await expect(link).toHaveValue(
    `${new URL(baseURL!).origin}/?q=Lumen#collection`,
  );
  await expect(link).toHaveAttribute("readonly", "");
  await expect(link).toBeFocused();
  expect(
    await link.evaluate((input: HTMLInputElement) =>
      input.value.slice(input.selectionStart ?? 0, input.selectionEnd ?? 0),
    ),
  ).toBe(`${new URL(baseURL!).origin}/?q=Lumen#collection`);
  await expect(page.getByText("Collection link copied.")).toHaveCount(0);
});

test("a late clipboard completion does not claim a changed selection was copied", async ({
  page,
  baseURL,
}) => {
  await page.goto("/?q=Studio");
  await ready(page, "34 objects · Page 1 of 2");
  await replaceClipboard(page, "deferred");
  await page.getByRole("button", { name: "Share results" }).click();
  await expect(
    page.getByRole("button", { name: "Share results" }),
  ).toBeDisabled();

  await stock(page).click();
  await ready(page, "30 objects · Page 1 of 2");
  await expect(
    page.getByRole("button", { name: "Share results" }),
  ).toBeEnabled();

  await page.evaluate(async () => {
    const win = window as unknown as { resolveCopy: () => void };
    win.resolveCopy();
    await new Promise((resolve) =>
      requestAnimationFrame(() => requestAnimationFrame(resolve)),
    );
  });
  await expect(page.getByText("Collection link copied.")).toHaveCount(0);
  await expect(page.getByText("Couldn’t copy automatically")).toHaveCount(0);
  expect(
    await page.evaluate(() => (window as never as { copied: string }).copied),
  ).toBe(`${new URL(baseURL!).origin}/?q=Studio#collection`);

  await page.getByRole("button", { name: "Share results" }).click();
  await page.evaluate(() =>
    (window as unknown as { resolveCopy: () => void }).resolveCopy(),
  );
  await expect(page.getByText("Collection link copied.")).toBeVisible();
  expect(
    await page.evaluate(() => (window as never as { copied: string }).copied),
  ).toBe(`${new URL(baseURL!).origin}/?q=Studio&in_stock=1#collection`);
});

test("keyboard users search with Enter and keep focus; page links hand focus to results", async ({
  page,
}) => {
  await page.goto("/");
  await ready(page, `${total} objects · Page 1 of 3`);
  await search(page).focus();
  await page.keyboard.type("Lumen");
  await page.keyboard.press("Enter");
  await ready(page, "12 objects");
  await expect(search(page)).toBeFocused();
  await expect(search(page)).toHaveValue("Lumen");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("button", { name: "Search", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(stock(page)).toBeFocused();
  await page.keyboard.press("Space");
  await ready(page, "8 objects");
  expect(relative(page)).toBe("/?q=Lumen&in_stock=1");
  await page.keyboard.press("Tab");
  await expect(sortBox(page)).toBeFocused();

  await page.goto("/");
  await ready(page, `${total} objects · Page 1 of 3`);
  const next = pages(page).getByRole("link", { name: "Next" });
  await next.focus();
  await expect(next).toBeFocused();
  await page.keyboard.press("Enter");
  await ready(page, `${total} objects · Page 2 of 3`);
  await expect(status(page)).toBeFocused();
});

test("share, pagination and search controls are touch sized", async ({
  page,
}) => {
  await page.goto("/");
  await ready(page, `${total} objects · Page 1 of 3`);
  const targets = [
    page.getByRole("button", { name: "Share results" }),
    page.getByRole("button", { name: "Search", exact: true }),
    pages(page).getByRole("link", { name: "Next" }),
    pages(page).getByRole("link", { name: "Page 2" }),
  ];
  await pages(page).scrollIntoViewIfNeeded();
  for (const target of targets) {
    const box = await target.boundingBox();
    expect(box!.height).toBeGreaterThanOrEqual(40);
    expect(box!.width).toBeGreaterThanOrEqual(40);
  }
  const stockBox = await page.locator("label[for='in-stock']").boundingBox();
  expect(stockBox!.height).toBeGreaterThanOrEqual(44);
  const nextBox = await targets[2].boundingBox();
  expect(nextBox!.height).toBeGreaterThanOrEqual(44);
});

test("narrow layouts and states stay accessible", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 });
  for (const url of [
    "/",
    "/?page=2",
    "/?page=3&sort=price-desc",
    "/?q=Studio&in_stock=1",
    "/?page=9",
    "/?q=zzz",
    "/?page=bogus",
  ]) {
    await page.goto(url);
    await expect(status(page)).toBeVisible();
    await expectAccessibleLayout(page);
  }
  await page.goto("/?page=2");
  await ready(page, `${total} objects · Page 2 of 3`);
  const nav = await pages(page).boundingBox();
  expect(nav!.x).toBeGreaterThanOrEqual(0);
  expect(nav!.x + nav!.width).toBeLessThanOrEqual(320);
});

const categories = (page: Page) =>
  page.getByRole("navigation", { name: "Categories" });

test("category keeps search, stock and sort, resets the page, and is shareable", async ({
  page,
  context,
  baseURL,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"], {
    origin: baseURL,
  });
  await page.goto("/?page=2");
  await ready(page, `${total} objects · Page 2 of 3`);
  await categories(page)
    .getByRole("link", { name: "Lighting, 13 objects" })
    .click();
  await ready(page, "13 objects");
  expect(relative(page)).toBe("/?category=lighting");
  await expect(
    page.getByRole("navigation", { name: "Breadcrumb" }),
  ).toContainText("Lighting");
  await expect(cards(page).first()).toHaveText("Task Light");

  await search(page).fill("Lumen");
  await search(page).press("Enter");
  await ready(page, "12 objects");
  expect(relative(page)).toBe("/?category=lighting&q=Lumen");
  await stock(page).click();
  await ready(page, "8 objects");
  expect(relative(page)).toBe("/?category=lighting&q=Lumen&in_stock=1");
  await chooseSort(page, "Name");
  await ready(page, "8 objects");
  expect(relative(page)).toBe(
    "/?category=lighting&q=Lumen&in_stock=1&sort=name",
  );

  await page.getByRole("button", { name: "Share results" }).click();
  await expect(page.getByText("Collection link copied.")).toBeVisible();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(
    `${new URL(baseURL!).origin}/?category=lighting&q=Lumen&in_stock=1&sort=name#collection`,
  );

  await page.getByRole("link", { name: "Clear all filters" }).click();
  await ready(page, `${total} objects · Page 1 of 3`);
  expect(relative(page)).toBe("/");
});

test("unknown categories are not found and malformed ones reset", async ({
  page,
}) => {
  await page.goto("/?category=not-a-real-category&q=oak");
  await expect(
    page.getByRole("heading", { name: "That category doesn’t exist." }),
  ).toBeVisible();
  expect(relative(page)).toBe("/?category=not-a-real-category&q=oak");
  await page.getByRole("link", { name: "View all objects" }).click();
  await ready(page, "1 object");
  expect(relative(page)).toBe("/?q=oak");

  await page.goto("/?category=all");
  await expect(
    page.getByRole("heading", { name: "That category doesn’t exist." }),
  ).toBeVisible();

  await page.goto("/?category=Lighting");
  await ready(page, `${total} objects · Page 1 of 3`);
  await expect(page.getByText(notice, { exact: false })).toBeVisible();
  await expect(
    categories(page).getByRole("link", { name: "All, 60 objects" }),
  ).toHaveAttribute("aria-current", "page");
});

test("an empty category is distinct from a search with no matches", async ({
  page,
}) => {
  await page.goto("/?category=workspace-comforts&q=Lumen");
  await expect(
    page.getByRole("heading", { name: "No objects found." }),
  ).toBeVisible();
  await page.goto("/?category=workspace-comforts");
  await ready(page, "3 objects");
  expect(relative(page)).toBe("/?category=workspace-comforts");
});

test("product details name the category and the return link keeps it", async ({
  page,
}) => {
  await page.goto("/?category=lighting&sort=name");
  await ready(page, "13 objects");
  await page.getByRole("link", { name: /Task Light/ }).click();
  await expect(
    page.getByRole("heading", { name: "Task Light", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Everyday focus")).toHaveCount(0);
  await expect(
    page.getByRole("link", { name: "Lighting" }).first(),
  ).toHaveAttribute("href", "/?category=lighting&sort=name#collection");
  const back = page.getByRole("link", { name: "Back to the collection" });
  await expect(back).toHaveAttribute(
    "href",
    "/?category=lighting&sort=name#collection",
  );
  await back.click();
  await ready(page, "13 objects");
  expect(relative(page)).toBe("/?category=lighting&sort=name");
  await expect(search(page)).toHaveValue("");
});

test("category links are reachable from the keyboard on a narrow screen", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await page.goto("/");
  await ready(page, `${total} objects · Page 1 of 3`);
  const lighting = categories(page).getByRole("link", {
    name: "Lighting, 13 objects",
  });
  await lighting.scrollIntoViewIfNeeded();
  await lighting.focus();
  await expect(lighting).toBeFocused();
  const box = await lighting.boundingBox();
  expect(box!.height).toBeGreaterThanOrEqual(40);
  expect(box!.x).toBeGreaterThanOrEqual(0);
  expect(box!.x + box!.width).toBeLessThanOrEqual(320);
  await page.keyboard.press("Enter");
  await ready(page, "13 objects");
  expect(relative(page)).toBe("/?category=lighting");
  await expectAccessibleLayout(page);
});

test("desktop selection and page are accessible with the collection controls", async ({
  page,
}) => {
  await page.goto("/?q=Studio&in_stock=1&sort=price-asc&page=2");
  await ready(page, "30 objects · Page 2 of 2");
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});
