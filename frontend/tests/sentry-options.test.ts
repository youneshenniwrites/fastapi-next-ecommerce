import { describe, expect, it } from "vitest";
import {
  SENTRY_TUNNEL_ROUTE,
  clientSentryOptions,
  serverSentryOptions,
} from "../src/lib/sentry-options";

describe("sentry options", () => {
  it("builds client options with tunnel and no PII", () => {
    const options = clientSentryOptions({
      dsn: "https://key@o0.ingest.sentry.io/0",
      environment: "production",
      nodeEnv: "production",
    });
    expect(options).toEqual({
      dsn: "https://key@o0.ingest.sentry.io/0",
      environment: "production",
      tracesSampleRate: 0.1,
      sendDefaultPii: false,
      tunnel: SENTRY_TUNNEL_ROUTE,
    });
  });

  it("builds server options without tunnel", () => {
    const options = serverSentryOptions({
      dsn: "https://key@o0.ingest.sentry.io/0",
      nodeEnv: "development",
    });
    expect(options).toEqual({
      dsn: "https://key@o0.ingest.sentry.io/0",
      environment: "development",
      tracesSampleRate: 1,
      sendDefaultPii: false,
    });
  });

  it("treats a missing DSN as disabled without crashing", () => {
    for (const builder of [clientSentryOptions, serverSentryOptions]) {
      expect(builder({}).dsn).toBeUndefined();
      expect(builder({ dsn: "" }).dsn).toBeUndefined();
    }
  });

  it("falls back to production environment without hints", () => {
    expect(serverSentryOptions({}).environment).toBe("production");
  });

  it("honors an explicit sample-rate override", () => {
    expect(
      clientSentryOptions({ nodeEnv: "development", tracesSampleRate: 0.5 })
        .tracesSampleRate,
    ).toBe(0.5);
  });
});
