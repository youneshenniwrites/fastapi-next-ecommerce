import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/browser",
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: { trace: "retain-on-failure", screenshot: "only-on-failure" },
  projects: [
    ...["Desktop Chrome", "Pixel 7"].map((device) => ({
      name: `account-${device}`,
      testMatch: "account.spec.ts",
      use: {
        ...devices[device],
        baseURL: "http://127.0.0.1:3300",
        trace: "off" as const,
        screenshot: "off" as const,
      },
    })),
    {
      name: "sessions",
      testMatch: "session.spec.ts",
      use: {
        baseURL: "http://127.0.0.1:3300",
        trace: "off",
        screenshot: "off",
      },
    },
    {
      name: "desktop",
      testMatch: "catalog.spec.ts",
      use: { ...devices["Desktop Chrome"], baseURL: "http://127.0.0.1:3300" },
    },
    {
      name: "cart-desktop",
      testMatch: "cart.spec.ts",
      use: { ...devices["Desktop Chrome"], baseURL: "http://127.0.0.1:3300" },
    },
    {
      name: "cart-mobile",
      testMatch: "cart.spec.ts",
      use: { ...devices["Pixel 7"], baseURL: "http://127.0.0.1:3300" },
    },
    {
      name: "mobile",
      testMatch: "catalog.spec.ts",
      use: { ...devices["Pixel 7"], baseURL: "http://127.0.0.1:3300" },
    },
    {
      name: "failure-states",
      testMatch: "states.spec.ts",
      use: { ...devices["Desktop Chrome"], baseURL: "http://127.0.0.1:3301" },
    },
  ],
  webServer: [
    {
      command: "../backend/.venv/bin/python scripts/test-api.py",
      url: "http://127.0.0.1:18300/health",
      reuseExistingServer: false,
      timeout: 60000,
    },
    {
      command: "node scripts/fault-api.mjs",
      url: "http://127.0.0.1:18301/health",
      reuseExistingServer: false,
    },
    {
      command: "npm run start",
      url: "http://127.0.0.1:3300",
      env: {
        API_BASE_URL: "http://127.0.0.1:18300",
        PORT: "3300",
        APP_ORIGIN: "http://127.0.0.1:3300",
        ALLOW_LOCAL_HTTP_SESSIONS: "true",
        HOSTNAME: "127.0.0.1",
      },
      reuseExistingServer: false,
      timeout: 60000,
    },
    {
      command: "npm run start",
      url: "http://127.0.0.1:3301",
      env: {
        API_BASE_URL: "http://127.0.0.1:18301",
        PORT: "3301",
        HOSTNAME: "127.0.0.1",
      },
      reuseExistingServer: false,
      timeout: 60000,
    },
  ],
});
