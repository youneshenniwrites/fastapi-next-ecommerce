import { describe, expect, it } from "vitest";
import { cn } from "../src/lib/utils";

describe("shared class composition", () => {
  it("keeps enabled conditional classes and removes conflicting utilities", () => {
    expect(
      cn(
        "px-2 text-sm",
        ["font-bold", false],
        { hidden: false, block: true },
        "px-4",
      ),
    ).toBe("text-sm font-bold block px-4");
  });

  it("preserves independent responsive and interaction variants", () => {
    expect(
      cn("px-2 sm:px-4 hover:bg-red-500", "sm:px-6 hover:bg-blue-500"),
    ).toBe("px-2 sm:px-6 hover:bg-blue-500");
    expect(cn(undefined, null, false)).toBe("");
  });
});
