// Browser-test-only fault server. Never imported by the application.
import { createServer } from "node:http";
let mode = "empty";
createServer((req, res) => {
  const path = new URL(req.url, "http://127.0.0.1").pathname;
  // Real loopback document: route.fulfill() has an unknown address space and
  // Chromium's local-network check would block the frame before CSP can run.
  if (path === "/frame-probe") {
    res.setHeader("Content-Type", "text/html");
    res.end(
      '<!doctype html><iframe src="http://127.0.0.1:3300/login"></iframe>',
    );
    return;
  }
  if (req.method === "POST" && path.startsWith("/scenario/")) {
    mode = path.split("/").at(-1);
    res.end("ok");
    return;
  }
  res.setHeader("Content-Type", "application/json");
  if (path === "/health") {
    res.end("{}");
    return;
  }
  if (mode === "error") {
    res.statusCode = 503;
    res.end('{"detail":"unavailable"}');
    return;
  }
  if (path === "/api/v1/categories" || path === "/api/v1/categories/") {
    res.end("[]");
    return;
  }
  if (path === "/api/v1/products/search") {
    const skip = Number(
      new URL(req.url, "http://127.0.0.1").searchParams.get("skip"),
    );
    const page = (total) =>
      JSON.stringify({ items: [], total, limit: 24, skip: skip || 0 });
    if (mode === "slow") {
      setTimeout(() => res.end(page(0)), 1500);
      return;
    }
    // A shared link can outlive the data that made its page number valid.
    res.end(page(mode === "range" ? 30 : 0));
    return;
  }
  if (path.startsWith("/api/v1/products/")) {
    if (path !== "/api/v1/products/") {
      res.statusCode = 404;
      res.end('{"detail":"not found"}');
      return;
    }
    if (mode === "slow") {
      setTimeout(() => res.end("[]"), 1500);
      return;
    }
    res.end("[]");
    return;
  }
  res.statusCode = 404;
  res.end("{}");
}).listen(18301, "127.0.0.1");
