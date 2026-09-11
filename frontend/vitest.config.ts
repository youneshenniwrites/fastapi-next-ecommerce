import { defineConfig } from "vitest/config";
export default defineConfig({
  test: {
    include: ["tests/**/*.test.ts"],
    coverage: {
      provider: "v8",
      include: [
        "src/lib/catalog.ts",
        "src/lib/session.ts",
        "src/lib/cart.ts",
        "src/lib/cart-validation.ts",
      ],
      reporter: ["text", "lcov"],
      thresholds: { statements: 95, branches: 90, functions: 100, lines: 95 },
    },
  },
});
