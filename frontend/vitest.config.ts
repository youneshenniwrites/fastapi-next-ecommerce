import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";
import scope from "./coverage-scope.json";
export default defineConfig({
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  test: {
    include: ["tests/**/*.test.{ts,tsx}"],
    coverage: {
      provider: "v8",
      include: scope.include,
      exclude: scope.exclude,
      reporter: ["text", "lcov"],
      thresholds: {
        statements: 95,
        branches: 90,
        functions: 100,
        lines: 95,
        "src/lib/{catalog,session}.ts": {
          statements: 95,
          branches: 90,
          functions: 100,
          lines: 95,
        },
      },
    },
  },
});
