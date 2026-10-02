import { NextRequest, NextResponse } from "next/server";
import { storefrontPolicy } from "./lib/security-headers";

export function proxy(request: NextRequest) {
  const headers = new Headers(request.headers);
  // Every route crosses Proxy so callers cannot choose the private render policy,
  // including framework/tunnel paths that do not need their own renderer nonce.
  headers.delete("x-vindor-render-csp");
  headers.delete("content-security-policy");
  headers.delete("content-security-policy-report-only");
  headers.delete("x-nonce");
  const path = request.nextUrl.pathname;
  if (
    path.startsWith("/_next/static/") ||
    path === "/_next/image" ||
    path === "/sentry-tunnel"
  )
    return NextResponse.next({ request: { headers } });
  const nonce = Buffer.from(
    crypto.getRandomValues(new Uint8Array(16)),
  ).toString("base64");
  const policy = storefrontPolicy(
    nonce,
    process.env.NODE_ENV === "development",
  );
  // Only our freshly generated nonce controls Next's renderer.
  headers.set("content-security-policy", policy);
  headers.set("x-vindor-render-csp", policy);
  headers.set("x-nonce", nonce);
  const response = NextResponse.next({ request: { headers } });
  // Enforce the verified nonce policy; renderer and response use the same value.
  response.headers.set("Content-Security-Policy", policy);
  // Public photos keep their cache policy. Missing-photo HTML is rendered
  // dynamically by the root layout and receives Next's private/no-store policy.
  if (!request.nextUrl.pathname.startsWith("/photos/"))
    response.headers.set("Cache-Control", "private, no-store");
  return response;
}

export const config = {
  matcher: ["/:path*"],
};
