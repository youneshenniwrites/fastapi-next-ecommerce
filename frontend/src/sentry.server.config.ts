import * as Sentry from "@sentry/nextjs";
import { serverSentryOptions } from "./lib/sentry-options";

Sentry.init(
  serverSentryOptions({
    dsn: process.env.SENTRY_DSN,
    environment: process.env.SENTRY_ENVIRONMENT,
    nodeEnv: process.env.NODE_ENV,
  }),
);
