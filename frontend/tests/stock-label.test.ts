import { expect, it } from "vitest";
import { stockLabel } from "../src/lib/stock-label";

it("names the available quantity", () => {
  expect(stockLabel(0)).toBe("Out of stock");
  expect(stockLabel(1)).toBe("1 in stock");
  expect(stockLabel(12)).toBe("12 in stock");
});
