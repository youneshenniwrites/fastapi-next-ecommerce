// @vitest-environment jsdom
import { expect, it } from "vitest";
import {
  init,
  getDefaultIntegrations,
  browserTracingIntegration,
  captureException,
  setUser,
  startSpan,
} from "@sentry/browser";
import { serializeEnvelope } from "@sentry/core";
import { clientSentryOptions } from "../src/lib/sentry-options";

it("keeps default error/tracing capture without emitting identity-bearing sessions", async () => {
  const payloads: string[] = [];
  const options = clientSentryOptions({
    dsn: "https://key@o0.ingest.sentry.io/0",
    environment: "privacy-test",
    tracesSampleRate: 1,
  });
  const defaults = getDefaultIntegrations(options);
  // Positive control: the installed SDK really would enable this channel.
  expect(defaults.some((item) => item.name === "BrowserSession")).toBe(true);
  const client = init({
    ...options,
    release: "demo@session-test",
    defaultIntegrations: [
      ...defaults,
      browserTracingIntegration({
        instrumentPageLoad: false,
        instrumentNavigation: false,
      }),
    ],
    transport: () => ({
      send: async (envelope) => {
        const serialized = serializeEnvelope(envelope);
        payloads.push(
          typeof serialized === "string"
            ? serialized
            : new TextDecoder().decode(serialized),
        );
        return { statusCode: 200 };
      },
      flush: async () => true,
    }),
  });
  if (!client) throw new Error("Browser SDK did not initialize");
  try {
    expect(client.getIntegrationByName("BrowserSession")).toBeUndefined();
    expect(client.getIntegrationByName("BrowserTracing")).toBeDefined();
    setUser({
      id: "fictional-secret",
      email: "fictional-secret@example.test",
      ip_address: "192.0.2.1",
    });
    window.history.pushState({}, "", "/privacy-check?secret=fictional-secret");
    document.dispatchEvent(new Event("visibilitychange"));
    captureException(new TypeError("fictional-secret"));
    startSpan(
      { name: "fictional-secret", op: "test", forceTransaction: true },
      () => {},
    );
    await client.flush();
    const serialized = payloads.join("\n");
    expect(serialized).toContain('"type":"event"');
    expect(serialized).toContain('"type":"transaction"');
    expect(serialized).toContain("TypeError");
    expect(serialized).toContain("demo@session-test");
    expect(serialized).not.toContain('"type":"session"');
    expect(serialized).not.toContain("fictional-secret");
    expect(serialized).not.toContain("192.0.2.1");
  } finally {
    setUser(null);
    await client.close();
  }
});
