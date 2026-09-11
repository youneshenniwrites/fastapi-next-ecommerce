import { describe, expect, it } from "vitest";
import { accountSchema } from "../src/lib/account-validation";

describe("account validation", () => {
  it("rejects empty fields and malformed email", () => {
    for (const mode of ["login", "register"] as const) {
      expect(
        accountSchema(mode).safeParse({ email: "", password: "" }).success,
      ).toBe(false);
      expect(
        accountSchema(mode).safeParse({
          email: "invalid",
          password: "password123",
        }).success,
      ).toBe(false);
    }
  });
  it("preserves login compatibility and registration boundaries", () => {
    for (const [mode, min, max] of [
      ["login", 1, 1024],
      ["register", 8, 128],
    ] as const) {
      const valid = (n: number) =>
        accountSchema(mode).safeParse({
          email: "test@example.com",
          password: "x".repeat(n),
        }).success;
      expect(valid(min - 1)).toBe(false);
      expect(valid(min)).toBe(true);
      expect(valid(max)).toBe(true);
      expect(valid(max + 1)).toBe(false);
    }
  });
  it("trims email but preserves password whitespace", () => {
    expect(
      accountSchema("login").parse({
        email: " test@example.com ",
        password: " secret ",
      }),
    ).toEqual({ email: "test@example.com", password: " secret " });
  });
});
