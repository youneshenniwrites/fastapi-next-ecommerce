// Disposable browser-fixture preload: simulate an edge that removes response-only
// CSP header names from the internal request handoff. Never used by deployments.
const http = require("node:http");
const original = http.Server.prototype.emit;
const stripped = new Set([
  "content-security-policy",
  "content-security-policy-report-only",
]);
http.Server.prototype.emit = function (event, ...args) {
  if (event === "request") {
    const request = args[0];
    for (const name of stripped) delete request.headers[name];
    const headers = new Proxy(request.headers, {
      set(target, key, value) {
        // Also strip the values Next's internal Proxy forwarding later writes.
        return stripped.has(key) || Reflect.set(target, key, value);
      },
    });
    Object.defineProperty(request, "headers", {
      configurable: true,
      get: () => headers,
      set: (value) => {
        for (const name of stripped) delete value[name];
        for (const key of Object.keys(headers)) delete headers[key];
        Object.assign(headers, value);
      },
    });
  }
  return original.call(this, event, ...args);
};
