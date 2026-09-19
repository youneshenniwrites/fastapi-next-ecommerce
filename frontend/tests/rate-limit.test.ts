import { describe, expect, it } from "vitest";
import { rateLimitMessage, retryAfterSeconds } from "../src/lib/rate-limit";

describe("retry timing", () => {
  it.each([
    ["0", 0],
    ["1", 1],
    [" 60 ", 60],
    ["86400", 86400],
  ] as const)("accepts delta %s", (input, expected) => {
    expect(retryAfterSeconds(input)).toBe(expected);
  });
  it.each([
    null,
    "",
    "-1",
    "1.5",
    "1e3",
    "Infinity",
    "86401",
    "999999999999999999999",
    "junk",
    "2026-09-19",
  ])("rejects %s", (input) => {
    expect(retryAfterSeconds(input)).toBeUndefined();
  });
  it("normalizes an HTTP date and clamps expired dates to zero", () => {
    const now = Date.parse("Sat, 19 Sep 2026 12:00:00 GMT");
    expect(retryAfterSeconds("Sat, 19 Sep 2026 12:00:12 GMT", now)).toBe(12);
    expect(retryAfterSeconds("Sat, 19 Sep 2026 11:59:00 GMT", now)).toBe(0);
  });
  it.each(["Saturday, 19-Sep-26 12:00:12 GMT", "Sat Sep 19 12:00:12 2026"])(
    "normalizes obsolete HTTP date %s",
    (input) => {
      expect(retryAfterSeconds(input, Date.parse("2026-09-19T12:00:00Z"))).toBe(
        12,
      );
    },
  );
  it("interprets obsolete two-digit years relative to the current century", () => {
    expect(
      retryAfterSeconds(
        "Saturday, 19-Sep-76 12:00:12 GMT",
        Date.parse("2076-09-19T12:00:00Z"),
      ),
    ).toBe(12);
  });
  it.each([
    "Sat Sep 32 12:00:12 2026",
    "Saturday, 32-Sep-26 12:00:12 GMT",
    "Sat Sep 19 12:00:12 2026 junk",
  ])("rejects malformed obsolete date %s", (input) => {
    expect(retryAfterSeconds(input)).toBeUndefined();
  });
  it("handles century rollover and rejects future waits beyond one day", () => {
    expect(
      retryAfterSeconds(
        "Saturday, 01-Jan-00 00:00:01 GMT",
        Date.parse("1999-12-31T23:59:59Z"),
      ),
    ).toBe(2);
    expect(
      retryAfterSeconds(
        "Saturday, 19-Sep-26 12:00:12 GMT",
        Date.parse("2026-09-17T12:00:00Z"),
      ),
    ).toBeUndefined();
    expect(
      retryAfterSeconds(
        "Sunday, 19-Sep-76 12:00:12 GMT",
        Date.parse("2026-09-19T12:00:00Z"),
      ),
    ).toBe(0);
  });
  it("uses fixed safe copy with singular/plural and fallback", () => {
    expect(rateLimitMessage()).toBe(
      "Too many requests. Wait briefly, then try again.",
    );
    expect(rateLimitMessage(1)).toContain("1 second,");
    expect(rateLimitMessage(12)).toContain("12 seconds,");
  });
});
