import { expect, type Locator, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Mobile browsers may expand innerWidth when content overflows. Compare to the
// configured viewport, which stays fixed even when that bug occurs.
export async function expectAccessibleLayout(page: Page) {
  await expect
    .poll(() => page.evaluate(() => document.documentElement.scrollWidth))
    .toBeLessThanOrEqual(page.viewportSize()!.width);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
}

export async function keyboardActivate(page: Page, control: Locator) {
  await expect(control).toBeVisible();
  await expect(control).toBeEnabled();
  // Exercise actual tab order rather than assigning focus programmatically.
  for (let attempt = 0; attempt < 80; attempt++) {
    if (await control.evaluate((node) => node === document.activeElement))
      break;
    await page.keyboard.press("Tab");
  }
  await expect(control).toBeFocused();
  await expect(control).toHaveCSS("outline-style", "solid");
  await expect(control).toHaveCSS("outline-width", "2px");
  await page.keyboard.press("Enter");
}
