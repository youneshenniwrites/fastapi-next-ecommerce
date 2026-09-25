import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs";
import {
  SENTRY_TUNNEL_ROUTE,
  sourceMapUploadEnabled,
} from "./src/lib/sentry-options";
const config: NextConfig = {
  poweredByHeader: false,
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
