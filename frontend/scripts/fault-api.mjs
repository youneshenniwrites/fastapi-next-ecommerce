// Browser-test-only fault server. Never imported by the application.
import { createServer } from "node:http";
let mode = "empty";
createServer((req, res) => {
  const path = new URL(req.url, "http://127.0.0.1").pathname;
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
