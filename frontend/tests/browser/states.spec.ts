import { test, expect } from "@playwright/test";
test("empty catalog and upstream failure are distinct and recoverable", async ({
  page,
  request,
}) => {
  await request.post("http://127.0.0.1:18301/scenario/empty");
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "A little space for something new." }),
  ).toBeVisible();
  await request.post("http://127.0.0.1:18301/scenario/error");
  await page.reload();
  await expect(
    page.getByRole("alert", { name: "Catalog unavailable" }),
  ).toContainText("We couldn’t reach the catalog");
  await request.post("http://127.0.0.1:18301/scenario/empty");
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(
    page.getByRole("heading", { name: "A little space for something new." }),
  ).toBeVisible();
});
test("loading state is visible while catalog fetch is pending", async ({
  page,
  request,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await request.post("http://127.0.0.1:18301/scenario/slow");
  await page.goto("/", { waitUntil: "commit" });
  await expect(
    page.getByRole("status", { name: "Loading collection" }),
  ).toBeVisible();
  await expect(page.locator('[data-slot="skeleton"]').first()).toHaveCSS(
    "animation-name",
    "none",
  );
  await expect(
    page.getByRole("heading", { name: "A little space for something new." }),
  ).toBeVisible();
  await request.post("http://127.0.0.1:18301/scenario/empty");
});
