import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";
import { proxy } from "../src/proxy";
import { storefrontPolicy } from "../src/lib/security-headers";

describe("storefront CSP rollout", () => {
  it("replaces caller-selected render policy and issues a fresh nonce per request", () => {
    const request = new NextRequest("https://shop.example/login", {
      headers: {
        "content-security-policy": "script-src 'unsafe-inline'",
        "content-security-policy-report-only": "script-src 'nonce-attacker'",
        "x-nonce": "attacker",
        "x-vindor-render-csp": "script-src 'nonce-attacker'",
      },
    });
    const first = proxy(request);
    const second = proxy(request);
    const policy = first.headers.get("content-security-policy-report-only")!;
    const nonce = policy.match(/'nonce-([^']+)'/)![1];
    expect(Buffer.from(nonce, "base64")).toHaveLength(16);
    expect(policy).not.toContain("attacker");
    expect(policy).not.toContain("script-src 'unsafe-inline'");
    expect(second.headers.get("content-security-policy-report-only")).not.toBe(
      policy,
    );
    expect(
      first.headers.get("x-middleware-request-content-security-policy"),
    ).toBe(policy);
    expect(first.headers.get("x-middleware-request-x-nonce")).toBe(nonce);
    expect(first.headers.get("x-middleware-request-x-vindor-render-csp")).toBe(
      policy,
    );
    expect(
      first.headers.get(
        "x-middleware-request-content-security-policy-report-only",
      ),
    ).toBeNull();
    expect(first.headers.get("cache-control")).toBe("private, no-store");
  });
  it("strips caller policy even on excluded resources without changing cache", () => {
    for (const path of [
      "/_next/static/not-a-file",
      "/_next/image",
      "/sentry-tunnel",
    ]) {
      const response = proxy(
        new NextRequest("https://shop.example" + path, {
          headers: {
            "x-vindor-render-csp": "script-src 'nonce-attacker'",
            "x-nonce": "attacker",
            "content-security-policy": "script-src 'nonce-attacker'",
            "content-security-policy-report-only":
              "script-src 'nonce-attacker'",
          },
        }),
      );
      for (const name of [
        "x-vindor-render-csp",
        "x-nonce",
        "content-security-policy",
        "content-security-policy-report-only",
      ])
        expect(response.headers.get("x-middleware-request-" + name)).toBeNull();
      expect(response.headers.get("cache-control")).toBeNull();
      expect(
        response.headers.get("content-security-policy-report-only"),
      ).toBeNull();
    }
  });
  it("keeps production scripts strict and development eval explicitly limited", () => {
    const production = storefrontPolicy("fixture", false);
    expect(production).toContain(
      "script-src 'self' 'nonce-fixture' 'strict-dynamic';",
    );
    expect(production).not.toContain("unsafe-eval");
    expect(production).toContain("connect-src 'self'");
    expect(production).toContain("object-src 'none'");
    expect(production).toContain("form-action 'self'");
    expect(storefrontPolicy("fixture", true)).toContain("'unsafe-eval'");
    expect(production).not.toContain("report-uri");
  });
});
