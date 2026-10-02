import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs";
import {
  SENTRY_TUNNEL_ROUTE,
  sourceMapUploadEnabled,
} from "./src/lib/sentry-options";
const config: NextConfig = {
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Content-Security-Policy", value: "frame-ancestors 'none'" },
          { key: "Strict-Transport-Security", value: "max-age=31536000" },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
        ],
      },
    ];
  },
  // A public build identifier, not a credential. Both runtimes use the same
  // build-time value even if server environment variables later change.
  env: { NEXT_PUBLIC_SENTRY_RELEASE: process.env.SENTRY_RELEASE || "" },
  // Vercel's adapter packages functions; standalone output is for local containers.
  output: process.env.VERCEL === "1" ? undefined : "standalone",
};
// Source-map upload stays disabled until the owner provides SENTRY_AUTH_TOKEN;
// builds must succeed on secrets-free checkouts and CI.
export default withSentryConfig(config, {
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,
  silent: true,
  widenClientFileUpload: true,
  tunnelRoute: SENTRY_TUNNEL_ROUTE,
  sourcemaps: { disable: !sourceMapUploadEnabled(process.env) },
});
