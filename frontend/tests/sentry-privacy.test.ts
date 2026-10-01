import { describe, expect, it } from "vitest";
import { NodeClient, defaultStackParser } from "@sentry/node";
import { BrowserClient } from "@sentry/browser";
import { serializeEnvelope, withScope, startSpan } from "@sentry/core";
import {
  serverSentryOptions,
  clientSentryOptions,
} from "../src/lib/sentry-options";
import {
  scrubError,
  scrubLog,
  scrubTransaction,
} from "../src/lib/sentry-privacy";

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
          release: "demo@1",
        }),
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
            op: "http.server",
            parent_span_id: "d".repeat(16),
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
            op: "http.client",
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
          {
            name: "fictional-secret",
            op: "http.server",
            forceTransaction: true,
            attributes: {
              "http.request.method": "GET",
              "http.response.status_code": 200,
              "url.full":
                "https://user:fictional-secret@shop.invalid/private?token=fictional-secret",
            },
          },
          () => {
            startSpan(
              { name: "fictional-secret", op: "fictional-secret" },
              () => {},
            );
            startSpan(
              {
                name: "https://shop.invalid/fictional-secret",
                op: "http.client",
                attributes: {
                  "http.method": "POST",
                  "http.status_code": 401,
                  "http.response.status_code": 401,
                  "http.url":
                    "https://user:fictional-secret@shop.invalid/?token=fictional-secret",
                },
              },
              () => {},
            );
            for (const [method, status] of [
              ["PROPFIND", "401"],
              ["GET\nfictional-secret", true],
            ])
              startSpan(
                {
                  name: "fictional-secret",
                  op: "http.client",
                  attributes: {
                    "http.method": method,
                    "http.response.status_code": status,
                  },
                },
                () => {},
              );
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
        "d".repeat(16),
        "Storefront request",
        "API request",
        "Application operation",
        "GET · Storefront request",
        "POST · API request",
        '"http.request.method":"GET"',
        '"http.method":"POST"',
        '"http.response.status_code":401',
        '"http.status_code":401',
      ]) {
        expect(serialized).toContain(diagnostic);
      }
      const transactions = payloads
        .map((payload) => JSON.parse(payload.split("\n")[2]))
        .filter((event) => event.type === "transaction");
      const generated = transactions.find(
        (event) => event.transaction === "GET · Storefront request",
      );
      expect(generated.contexts.trace.data).toEqual({
        "http.request.method": "GET",
        "http.response.status_code": 200,
      });
      expect(
        generated.spans
          .filter((span: { op: string }) => span.op === "http.client")
          .map((span: { data?: unknown }) => span.data),
      ).toEqual([
        {
          "http.method": "POST",
          "http.status_code": 401,
          "http.response.status_code": 401,
        },
        { "http.method": "_OTHER" },
        undefined,
      ]);
      await client.close();
    },
  );
});

it.each(["http.method", "http.request.method"])(
  "validates the finite method vocabulary in %s",
  (key) => {
    for (const method of [
      "GET",
      "HEAD",
      "POST",
      "PUT",
      "DELETE",
      "CONNECT",
      "OPTIONS",
      "TRACE",
      "PATCH",
      "get",
      "PROPFIND",
      "fictional-secret",
    ])
      expect(
        scrubTransaction({
          contexts: { trace: { op: "http.server", data: { [key]: method } } },
        } as never).contexts?.trace?.data,
      ).toEqual({
        [key]:
          /^[A-Z]+$/.test(method) && method !== "PROPFIND" ? method : "_OTHER",
      });
    for (const method of [
      undefined,
      null,
      true,
      42,
      [],
      {},
      "",
      "GET POST",
      "GET\n",
      "GET\r\n",
      "https://shop.invalid/private?token=fictional-secret",
    ])
      expect(
        scrubTransaction({
          contexts: { trace: { op: "http.server", data: { [key]: method } } },
        } as never).contexts?.trace?.data,
      ).toBeUndefined();
  },
);

it.each(["http.response.status_code", "http.status_code"])(
  "keeps only integer HTTP response status in %s",
  (key) => {
    for (const status of [100, 200, 401, 599])
      expect(
        scrubTransaction({
          spans: [{ op: "http.client", data: { [key]: status } }],
        } as never).spans?.[0].data,
      ).toEqual({ [key]: status });
    for (const status of [
      undefined,
      null,
      true,
      "200",
      99,
      600,
      200.5,
      NaN,
      Infinity,
      {},
      [],
    ])
      expect(
        scrubTransaction({
          spans: [{ op: "http.client", data: { [key]: status } }],
        } as never).spans?.[0].data,
      ).toBeUndefined();
  },
);

it("does not invent HTTP fields or prefix non-HTTP span labels", () => {
  const clean = scrubTransaction({
    type: "transaction",
    transaction: "fictional-secret",
    contexts: { trace: { op: "http.server" } },
    request: { method: "GET", url: "fictional-secret" },
    spans: [
      {
        op: "ui.render",
        data: { "http.method": "GET", arbitrary: "fictional-secret" },
      },
      { op: "http.client", data: { "http.method": "PROPFIND" } },
    ],
  } as never);
  expect(clean.transaction).toBe("Storefront request");
  expect(clean.contexts?.trace?.data).toBeUndefined();
  expect(clean.spans?.map((s) => s.description)).toEqual([
    "Component render",
    "_OTHER · API request",
  ]);
  expect(JSON.stringify(clean)).not.toContain("fictional-secret");
});

it("uses a closed label vocabulary for malformed and malicious spans", () => {
  const event = {
    type: "transaction",
    transaction:
      "https://shop.invalid/fictional-secret?email=private@example.invalid",
    contexts: {
      trace: {
        op: "http.server",
        trace_id: "a".repeat(32),
        parent_span_id: "b".repeat(16),
      },
    },
    spans: [
      { op: "function.nextjs", description: "fictional-secret" },
      { op: "fictional-secret", description: "SELECT private@example.invalid" },
      { op: "__proto__", description: "fictional-secret" },
      null,
    ],
  };
  const clean = scrubTransaction(event as never);
  expect(clean.transaction).toBe("Storefront request");
  expect(clean.spans?.map((s) => s.description)).toEqual([
    "Next.js function",
    "Application operation",
    "Application operation",
    "Application operation",
  ]);
  expect(JSON.stringify(clean)).not.toMatch(
    /fictional-secret|private@example|SELECT|__proto__/,
  );
  expect(clean.contexts?.trace?.parent_span_id).toBe("b".repeat(16));
  expect(
    scrubError({ type: undefined, transaction: "private@example.invalid" })
      .transaction,
  ).toBe("[Filtered]");
});
