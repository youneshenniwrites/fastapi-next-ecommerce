import { describe, expect, it } from "vitest";
import {
  filterProducts,
  money,
  priceInPence,
  productArt,
  type Product,
} from "../src/lib/catalog";
const products: Product[] = [
  { id: 2, name: "Mat", price: "29.50", currency: "GBP", stock: 0 },
  { id: 1, name: "Stand", price: "79.00", currency: "GBP", stock: 3 },
  { id: 3, name: "Cup", price: "29.50", currency: "GBP", stock: 1 },
];
describe("GBP display and catalog controls", () => {
  it("preserves pennies and large amounts without float arithmetic", () => {
    expect(money("9999999999.99")).toBe("£9,999,999,999.99");
    expect(money("0.01")).toBe("£0.01");
    expect(money("0.00")).toBe("£0.00");
    expect(priceInPence("19.90")).toBe(1990n);
    for (const invalid of ["NaN", "-1.00", "1.234", "1", "1e3"])
      expect(() => money(invalid)).toThrow();
  });
  it("filters without mutating server data", () => {
    expect(
      filterProducts(products, " STAND ", true, "featured").map((p) => p.id),
    ).toEqual([1]);
    expect(
      filterProducts(products, "", true, "featured").map((p) => p.id),
    ).toEqual([1, 3]);
    expect(filterProducts(products, "absent", false, "featured")).toEqual([]);
    expect(products.map((p) => p.id)).toEqual([2, 1, 3]);
  });
  it("sorts numeric prices rather than strings, preserving ties", () => {
    expect(
      filterProducts(products, "", false, "price-asc").map((p) => p.id),
    ).toEqual([2, 3, 1]);
    expect(
      filterProducts(products, "", false, "price-desc").map((p) => p.id),
    ).toEqual([1, 2, 3]);
    expect(
      filterProducts(products, "", false, "name").map((p) => p.name),
    ).toEqual(["Cup", "Mat", "Stand"]);
  });
  it("uses demo artwork only for known names and a neutral fallback", () => {
    expect(productArt("Task Light")).toBe("/photos/lamp.webp");
    for (const name of ["Unrecognised product", "toString", "__proto__"])
      expect(productArt(name)).toBeUndefined();
  });
});
