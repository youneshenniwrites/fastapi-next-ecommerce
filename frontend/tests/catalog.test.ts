import { describe, expect, it } from "vitest";
import { existsSync } from "node:fs";
import { money, priceInPence, imageKeys, productArt } from "../src/lib/catalog";
describe("GBP display and catalog controls", () => {
  it("preserves pennies and large amounts without float arithmetic", () => {
    expect(money("9999999999.99")).toBe("£9,999,999,999.99");
    expect(money("0.01")).toBe("£0.01");
    expect(money("0.00")).toBe("£0.00");
    expect(priceInPence("19.90")).toBe(1990n);
    for (const invalid of ["NaN", "-1.00", "1.234", "1", "1e3"])
      expect(() => money(invalid)).toThrow();
  });
  it("uses an allowlisted photo key and a neutral fallback", () => {
    expect(productArt("lamp")).toBe("/photos/lamp.webp");
    expect(productArt("Task Light")).toBeUndefined();
    for (const key of [
      "toString",
      "__proto__",
      "https://evil.example/lamp.webp",
    ])
      expect(productArt(key)).toBeUndefined();
    for (const key of imageKeys)
      expect(existsSync(`public/photos/${key}.webp`)).toBe(true);
  });
});
