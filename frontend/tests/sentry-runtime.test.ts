import { afterEach, expect, it, vi } from "vitest";

const init = vi.hoisted(() => vi.fn());
vi.mock("@sentry/nextjs", () => ({
  init,
  captureRouterTransitionStart: vi.fn(),
  withSentryConfig: (config: unknown) => config,
}));

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
  init.mockClear();
});

it.each(["trusted-deployment-sha", ""])(
  "binds actual browser and server initializers to build release %s",
  async (release) => {
    vi.stubEnv("SENTRY_RELEASE", release);
    vi.stubEnv("SENTRY_AUTH_TOKEN", "fictional-secret");
    const config = (await import("../next.config")).default;
    expect(config.env).toEqual({ NEXT_PUBLIC_SENTRY_RELEASE: release });
    expect(JSON.stringify(config.env)).not.toContain("fictional-secret");
    vi.stubEnv(
      "NEXT_PUBLIC_SENTRY_RELEASE",
      config.env!.NEXT_PUBLIC_SENTRY_RELEASE!,
    );
    // Runtime drift must not assign a different server release from its browser.
    vi.stubEnv("SENTRY_RELEASE", "different-runtime-sha");
    await import("../src/instrumentation-client");
    await import("../src/sentry.server.config");
    expect(init).toHaveBeenCalledTimes(2);
    for (const [options] of init.mock.calls) {
      expect(options.release).toBe(release || undefined);
      expect(options.sendDefaultPii).toBe(false);
    }
  },
);
