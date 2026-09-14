import { describe, expect, it } from "vitest";
import { cartQuantitySchema } from "../src/lib/cart-validation";

describe("cart quantity schema", () => {
  it("accepts whole quantities from 1 to 99", () => {
    expect(cartQuantitySchema.safeParse({ quantity: 1 }).success).toBe(true);
    expect(cartQuantitySchema.safeParse({ quantity: 99 }).success).toBe(true);
  });

  it("rejects invalid and missing quantity input", () => {
    for (const input of [
      { quantity: 0 },
      { quantity: 100 },
      { quantity: 1.5 },
      { quantity: "2" },
      {},
    ]) {
      expect(cartQuantitySchema.safeParse(input).success).toBe(false);
    }
  });
});
