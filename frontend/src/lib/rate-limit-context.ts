import "server-only";
import { createHmac } from "node:crypto";
import { isIP } from "node:net";

type AuthPath = "/api/v1/auth/login" | "/api/v1/auth/register";

/** Carry Vercel's browser identity across the separate API ingress, without raw IPs. */
export function rateLimitContextHeaders(
  request: Request,
  path: AuthPath,
): Record<string, string> {
  const secret = process.env.RATE_LIMIT_PROXY_SECRET;
  if (
    process.env.VERCEL !== "1" ||
    !secret ||
    secret.length < 32 ||
    secret.trim() !== secret
  )
    return {};

  // Vercel overwrites this header at public ingress. Local/custom proxies are
  // deliberately unsupported; never select a caller-controlled chain entry.
  const address = request.headers.get("x-forwarded-for") ?? "";
  const version = isIP(address);
  if (!version || address.includes("%")) return {};
  const normalized =
    version === 6
      ? new URL(`http://[${address}]`).hostname.slice(1, -1)
      : address;
  const bucket = createHmac("sha256", secret)
    .update(`vindor-client:${normalized}`)
    .digest("hex");
  const timestamp = Math.floor(Date.now() / 1000);
  const signature = createHmac("sha256", secret)
    .update(`${timestamp}\n${bucket}\nPOST\n${path}`)
    .digest("hex");
  return {
    "x-vindor-client-context": `${timestamp}.${bucket}.${signature}`,
  };
}
