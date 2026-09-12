import { describe, expect, it } from "vitest";
import { CartOperations } from "@/lib/cart-operations";

describe("cart operation ownership", () => {
  it("admits B while A is stalled and ignores A's late completion", () => {
    const guard = new CartOperations("A");
    const old = guard.begin(1)!;
    expect(guard.begin(1)).toBeNull();
    guard.reset("B");
    const next = guard.begin(1)!;
    expect(next).not.toBeNull();
    expect(guard.current(1, old)).toBe(false);
    expect(guard.finish(1, old)).toBe(false);
    expect(guard.begin(1)).toBeNull();
    expect(guard.current(1, next)).toBe(true);
    expect(guard.finish(1, next)).toBe(true);
    expect(guard.begin(1)).not.toBeNull();
  });
  it("preserves same-owner guards but invalidates them across A/B/A", () => {
    const guard = new CartOperations("A");
    const old = guard.begin(1)!;
    guard.reset("A");
    expect(guard.current(1, old)).toBe(true);
    guard.reset(null);
    guard.reset("A");
    expect(guard.current(1, old)).toBe(false);
    expect(guard.begin(1)).not.toBeNull();
  });
});
