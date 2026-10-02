import assert from "node:assert/strict";
import http from "node:http";
import process from "node:process";
import {
  setTimeout,
  clearTimeout,
  setInterval,
  clearInterval,
} from "node:timers";
import { test } from "node:test";
import { apiClient } from "../src/lib/api/client.ts";

test("API deadlines survive Request copies and garbage collection through body reads", async () => {
  assert.equal(typeof globalThis.gc, "function", "run with --expose-gc");
  const nativeFetch = globalThis.fetch;
  const previousOrigin = process.env.API_BASE_URL;
  const released = new Set();
  const timers = [];
  const server = http.createServer((request, response) => {
    if (request.url === "/body") {
      response.writeHead(200, { "Content-Type": "application/json" });
      response.flushHeaders();
    }
    timers.push(
      setTimeout(() => {
        released.add(request.url);
        if (!response.headersSent)
          response.writeHead(200, { "Content-Type": "application/json" });
        response.end("[]");
      }, 6000),
    );
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  process.env.API_BASE_URL = `http://127.0.0.1:${server.address().port}`;
  // The installed Next fetch wrapper copies Request + init into effective
  // Requests. Force GC to reproduce lost signal propagation deterministically.
  globalThis.fetch = (request, init) => {
    const effective = new globalThis.Request(request, init);
    return nativeFetch(new globalThis.Request(effective.url, effective));
  };
  const gc = setInterval(() => globalThis.gc(), 30);
  try {
    await Promise.all(
      ["/headers", "/body"].map(async (path) => {
        await assert.rejects(apiClient().GET(path), { name: "TimeoutError" });
        assert.equal(
          released.has(path),
          false,
          "must time out before the delayed response is released",
        );
      }),
    );
  } finally {
    clearInterval(gc);
    timers.forEach(clearTimeout);
    globalThis.fetch = nativeFetch;
    if (previousOrigin === undefined) delete process.env.API_BASE_URL;
    else process.env.API_BASE_URL = previousOrigin;
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
  }
});

test("Mutation acknowledgement timeouts survive installed Next Request copies", async () => {
  assert.equal(typeof globalThis.gc, "function", "run with --expose-gc");
  const nativeFetch = globalThis.fetch;
  const previousOrigin = process.env.API_BASE_URL;
  const released = new Set();
  const received = new Set();
  const timers = [];
  const server = http.createServer((request, response) => {
    received.add(request.url);
    if (request.url === "/body") {
      response.writeHead(200, { "Content-Type": "application/json" });
      response.flushHeaders();
    }
    timers.push(
      setTimeout(() => {
        released.add(request.url);
        if (!response.headersSent)
          response.writeHead(200, { "Content-Type": "application/json" });
        response.end("[]");
      }, 6000),
    );
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  process.env.API_BASE_URL = `http://127.0.0.1:${server.address().port}`;
  const { createPatchedFetcher } = (
    await import("next/dist/server/lib/patch-fetch.js")
  ).default;
  const workStore = {
    route: "/cart",
    isStaticGeneration: false,
    fetchCache: "force-no-store",
  };
  globalThis.fetch = createPatchedFetcher(nativeFetch, {
    workAsyncStorage: { getStore: () => workStore },
    workUnitAsyncStorage: { getStore: () => undefined },
  });
  const gc = setInterval(() => globalThis.gc(), 30);
  try {
    await Promise.all(
      ["/headers", "/body"].map(async (path) => {
        await assert.rejects(
          apiClient().PUT(path, {
            body: { quantity: 2 },
          }),
          { name: "TimeoutError" },
        );
        assert.equal(received.has(path), true);
        assert.equal(
          released.has(path),
          false,
          "must reject before acknowledgement arrives",
        );
      }),
    );
  } finally {
    clearInterval(gc);
    timers.forEach(clearTimeout);
    globalThis.fetch = nativeFetch;
    if (previousOrigin === undefined) delete process.env.API_BASE_URL;
    else process.env.API_BASE_URL = previousOrigin;
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
  }
});
