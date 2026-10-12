import { expect, it } from "vitest";
import {
  catalogProductId,
  productDocumentTitle,
} from "../src/lib/product-title";

it("uses the catalog name and rejects an invalid id", () => {
  expect(productDocumentTitle("Oak Monitor Stand")).toBe("Oak Monitor Stand");
  expect(productDocumentTitle("  ")).toBe("Not found");
  expect(productDocumentTitle(null)).toBe("Not found");
  expect(catalogProductId("1")).toBe(1);
  expect(catalogProductId("0")).toBeNull();
  expect(catalogProductId("9007199254740993")).toBeNull();
  expect(catalogProductId("not-an-id")).toBeNull();
});
