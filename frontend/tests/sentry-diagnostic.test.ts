import { afterEach, beforeEach, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
const runtime = vi.hoisted(() => ({
  token: "private-token",
  origin: "https://shop.test",
  capture: vi.fn(),
  flush: vi.fn(),
}));
vi.mock("next/headers", () => ({
  cookies: async () => ({
    get: () => (runtime.token ? { value: runtime.token } : undefined),
  }),
  headers: async () => new Headers({ origin: runtime.origin }),
}));
vi.mock("next/navigation", () => ({
  notFound: () => {
    throw new Error("404");
  },
}));
vi.mock("@sentry/nextjs", () => ({
  captureException: runtime.capture,
  flush: runtime.flush,
}));
import { requireSentryDiagnosticAdmin } from "../src/lib/sentry-diagnostic";
import {
  authorizeClientDiagnostic,
  captureServerDiagnostic,
} from "../src/app/diagnostics/sentry/actions";
import Page from "../src/app/diagnostics/sentry/page";

function identity(
  body: object = { is_active: true, is_superuser: true },
  status = 200,
) {
  const fetch = vi.fn(
    async () =>
      new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
  );
  vi.stubGlobal("fetch", fetch);
  return fetch;
}
beforeEach(() => {
  vi.stubEnv("APP_ORIGIN", "https://shop.test");
  vi.stubEnv("SENTRY_ENVIRONMENT", "development");
  vi.stubEnv("SENTRY_DIAGNOSTICS_ENABLED", "true");
  runtime.token = "private-token";
  runtime.origin = "https://shop.test";
  runtime.capture.mockReset();
  runtime.flush.mockReset().mockResolvedValue(true);
  identity();
});
afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

it.each([undefined, "false", "TRUE"])(
  "returns404 without explicit enabled flag %s",
  async (flag) => {
    vi.stubEnv("SENTRY_DIAGNOSTICS_ENABLED", flag);
    await expect(Page()).rejects.toThrow("404");
    await expect(captureServerDiagnostic()).rejects.toThrow("404");
    expect(runtime.capture).not.toHaveBeenCalled();
  },
);
it.each(["production", "preview", ""])(
  "returns404 outside development: %s",
  async (env) => {
    vi.stubEnv("SENTRY_ENVIRONMENT", env);
    await expect(authorizeClientDiagnostic()).rejects.toThrow("404");
  },
);
it("denies anonymous requests without querying API", async () => {
  runtime.token = "";
  const fetch = identity();
  await expect(requireSentryDiagnosticAdmin()).rejects.toThrow("404");
  expect(fetch).not.toHaveBeenCalled();
});
it.each([
  [{ is_active: true, is_superuser: false }, 200],
  [{ is_active: false, is_superuser: true }, 200],
  [{}, 401],
  [{ is_active: true, is_superuser: true }, 503],
])("denies non-admin/inactive/invalid identity %j", async (body, status) => {
  identity(body as object, status as number);
  await expect(captureServerDiagnostic()).rejects.toThrow("404");
  expect(runtime.capture).not.toHaveBeenCalled();
});
it.each(["", "https://attacker.test"])(
  "rejects action origin %s",
  async (origin) => {
    runtime.origin = origin;
    await expect(captureServerDiagnostic()).rejects.toThrow("404");
    expect(runtime.capture).not.toHaveBeenCalled();
  },
);
it("rechecks active administrator on every trigger and captures a fixed server error", async () => {
  const fetch = identity();
  expect(await Page()).toBeTruthy();
  expect(await authorizeClientDiagnostic()).toBe(true);
  expect(await captureServerDiagnostic()).toEqual({ flushed: true });
  expect(fetch).toHaveBeenCalledTimes(3);
  expect(runtime.capture).toHaveBeenCalledWith(
    expect.objectContaining({
      message: "Development server observability verification",
    }),
  );
  expect(runtime.flush).toHaveBeenCalledWith(2000);
  identity({ is_active: false, is_superuser: true });
  await expect(authorizeClientDiagnostic()).rejects.toThrow("404");
  expect(runtime.capture).toHaveBeenCalledTimes(1);
});
it("does not claim delivery when flush times out", async () => {
  runtime.flush.mockResolvedValue(false);
  expect(await captureServerDiagnostic()).toEqual({ flushed: false });
});

it("fails closed when the identity service cannot be reached", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockRejectedValue(new Error("Network unavailable")),
  );
  await expect(captureServerDiagnostic()).rejects.toThrow(
    "Network unavailable",
  );
  expect(runtime.capture).not.toHaveBeenCalled();
  expect(runtime.flush).not.toHaveBeenCalled();
});
