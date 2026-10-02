import { NextRequest, NextResponse } from "next/server";
import { storefrontPolicy } from "./lib/security-headers";

export function proxy(request: NextRequest) {
  const nonce = Buffer.from(
    crypto.getRandomValues(new Uint8Array(16)),
  ).toString("base64");
  const policy = storefrontPolicy(
    nonce,
    process.env.NODE_ENV === "development",
  );
  const headers = new Headers(request.headers);
  // Only our freshly generated nonce controls Next's renderer.
  headers.delete("content-security-policy-report-only");
  headers.set("content-security-policy", policy);
  headers.set("x-nonce", nonce);
  const response = NextResponse.next({ request: { headers } });
  // Report-only first; framing is already enforced by the baseline CSP/XFO.
  response.headers.set("Content-Security-Policy-Report-Only", policy);
  // Public photos keep their cache policy. Missing-photo HTML is rendered
  // dynamically by the root layout and receives Next's private/no-store policy.
  if (!request.nextUrl.pathname.startsWith("/photos/"))
    response.headers.set("Cache-Control", "private, no-store");
  return response;
}

export const config = {
  matcher: ["/((?!_next/static/|_next/image$|sentry-tunnel$).*)"],
};
