import { describe, expect, it } from "vitest";
import { NodeClient, defaultStackParser } from "@sentry/node";
import { BrowserClient } from "@sentry/browser";
import { serializeEnvelope, withScope, startSpan } from "@sentry/core";
import {
  serverSentryOptions,
  clientSentryOptions,
} from "../src/lib/sentry-options";
import { scrubError, scrubLog } from "../src/lib/sentry-privacy";

describe("Sentry payload privacy", () => {
  it("filters defensive log output", () => {
    const log = scrubLog({
      level: "error",
      message: "fictional-secret",
      attributes: { password: "fictional-secret", "sentry.release": "demo@1" },
    });
    expect(JSON.stringify(log)).not.toContain("fictional-secret");
    expect(log.attributes?.["sentry.release"]).toBe("demo@1");
  });
  it("drops arbitrary contexts but retains code identifiers", () => {
    const event = {
      type: undefined,
      exception: {
        values: [
          {
            type: "TypeError",
            value: "fictional-secret",
            stacktrace: {
              frames: [
                {
                  filename: "orders.ts",
                  function: "submitOrder",
                  lineno: 4,
                  vars: { password: "fictional-secret" },
                },
              ],
            },
          },
        ],
      },
      extra: { nested: [[{ password: "fictional-secret" }]] },
      request: {
        headers: { authorization: "fictional-secret" },
        url: "https://example.invalid/?token=fictional-secret",
      },
      breadcrumbs: [
        { message: "fictional-secret", data: { token: "fictional-secret" } },
      ],
    };
    const clean = scrubError(event);
    const mapped = scrubError({
      type: undefined,
      debug_meta: {
        images: [
          {
            type: "sourcemap",
            debug_id: "12345678-1234-1234-1234-123456789abc",
            code_file:
              "https://user:fictional-secret@example.invalid/_next/static/chunks/app.js?token=fictional-secret",
          },
        ],
      },
      exception: {
        values: [
          {
            stacktrace: {
              frames: [
                {
                  filename:
                    "https://example.invalid/_next/static/chunks/app.js?token=fictional-secret",
                },
              ],
            },
          },
        ],
      },
    });
    expect(mapped.debug_meta?.images?.[0]).toEqual({
      type: "sourcemap",
      debug_id: "12345678-1234-1234-1234-123456789abc",
      code_file: "/_next/static/chunks/app.js",
    });
    expect(mapped.exception?.values?.[0].stacktrace?.frames?.[0].filename).toBe(
      "/_next/static/chunks/app.js",
    );
    expect(JSON.stringify(mapped)).not.toContain("fictional-secret");
    expect(JSON.stringify(clean)).not.toContain("fictional-secret");
    expect(clean.exception?.values?.[0].stacktrace?.frames?.[0]).toEqual({
      filename: "orders.ts",
      function: "submitOrder",
      lineno: 4,
    });
    expect(event.exception.values[0].value).toBe("fictional-secret");
  });

  it.each(["server", "browser"])(
    "serializes %s SDK envelopes without private context",
    async (runtime) => {
      const payloads: string[] = [];
      const Client = runtime === "server" ? NodeClient : BrowserClient;
      const client = new Client({
        ...(runtime === "server" ? serverSentryOptions : clientSentryOptions)({
          dsn: "https://key@o0.ingest.sentry.io/0",
          environment: "privacy-test",
          tracesSampleRate: 1,
        }),
        release: "demo@1",
        integrations: [],
        stackParser: defaultStackParser,
        transport: () => ({
          send: async (envelope) => {
            const bytes = serializeEnvelope(envelope);
            payloads.push(
              typeof bytes === "string"
                ? bytes
                : new TextDecoder().decode(bytes),
            );
            return { statusCode: 200 };
          },
          flush: async () => true,
        }),
      });
      client.init();
      client.captureEvent({
        exception: {
          values: [{ type: "TypeError", value: "fictional-secret" }],
        },
        request: {
          data: "username=fictional-secret",
          headers: { cookie: "fictional-secret" },
        },
        extra: { password: "fictional-secret" },
      });
      client.captureEvent({
        type: "transaction",
        transaction: "fictional-secret",
        timestamp: 2,
        start_timestamp: 1,
        contexts: {
          trace: {
            trace_id: "a".repeat(32),
            span_id: "b".repeat(16),
            op: "test",
          },
          private: { password: "fictional-secret" },
        },
        spans: [
          {
            trace_id: "a".repeat(32),
            span_id: "c".repeat(16),
            start_timestamp: 1,
            timestamp: 2,
            description: "fictional-secret",
            data: { token: "fictional-secret" },
          },
        ],
      });
      withScope((scope) => {
        scope.setClient(client);
        scope.setExtra("private", { password: "fictional-secret" });
        scope.addBreadcrumb({ message: "fictional-secret" });
        client.captureException(new Error("fictional-secret"));
        startSpan(
          { name: "fictional-secret", op: "test", forceTransaction: true },
          () => {
            startSpan({ name: "fictional-secret", op: "child" }, () => {});
          },
        );
      });
      await client.flush();
      expect(payloads).toHaveLength(4);
      const serialized = payloads.join("\n");
      expect(serialized).not.toContain("fictional-secret");
      expect(serialized).toContain("sentry-privacy.test.ts");
      for (const diagnostic of [
        "TypeError",
        "privacy-test",
        "demo@1",
        "a".repeat(32),
        "b".repeat(16),
      ]) {
        expect(serialized).toContain(diagnostic);
      }
      await client.close();
    },
  );
});
