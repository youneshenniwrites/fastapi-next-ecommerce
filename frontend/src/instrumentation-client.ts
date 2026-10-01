import * as Sentry from "@sentry/nextjs";
import { clientSentryOptions } from "./lib/sentry-options";

Sentry.init(
  clientSentryOptions({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT,
    nodeEnv: process.env.NODE_ENV,
    release: process.env.NEXT_PUBLIC_SENTRY_RELEASE,
  }),
);

export const onRouterTransitionStart = Sentry.captureRouterTransitionStart;
