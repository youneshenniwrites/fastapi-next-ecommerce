import type { Client, Integration } from "@sentry/core";
import {
  scrubError,
  scrubLog,
  scrubSamplingTransaction,
  scrubStreamedSpan,
  scrubTransaction,
} from "./sentry-privacy";
export const SENTRY_TUNNEL_ROUTE = "/sentry-tunnel";

/** The stream envelope header is not passed through beforeSendSpan. */
export function vindorPrivacyIntegration(): Integration {
  return {
    name: "VindorPrivacy",
    setup(client: Client) {
      client.on(
        "createDsc",
        (dsc: { transaction?: string }, span?: unknown) => {
          dsc.transaction = scrubSamplingTransaction(dsc.transaction, span);
        },
      );
    },
  };
}

export interface SentryRuntimeEnv {
  dsn?: string;
  release?: string;
  environment?: string;
  nodeEnv?: string;
  tracesSampleRate?: number;
}

interface BaseSentryOptions {
  dsn: string | undefined;
  release: string | undefined;
  environment: string;
  tracesSampleRate: number;
  sendDefaultPii: false;
  beforeSend: typeof scrubError;
  beforeSendSpan: typeof scrubStreamedSpan;
  beforeSendTransaction: typeof scrubTransaction;
  beforeSendLog: typeof scrubLog;
}

export interface ClientSentryOptions extends BaseSentryOptions {
  tunnel: string;
  integrations: (defaults: Integration[]) => Integration[];
}

export type ServerSentryOptions = BaseSentryOptions;

function sampleRateFor(env: SentryRuntimeEnv): number {
  if (env.tracesSampleRate !== undefined) {
    return env.tracesSampleRate;
  }
  return env.nodeEnv === "development" ? 1 : 0.1;
}

function baseSentryOptions(env: SentryRuntimeEnv): BaseSentryOptions {
  return {
    dsn: env.dsn || undefined,
    release: env.release || undefined,
    environment: env.environment || env.nodeEnv || "production",
    tracesSampleRate: sampleRateFor(env),
    sendDefaultPii: false,
    beforeSend: scrubError,
    beforeSendSpan: scrubStreamedSpan,
    beforeSendTransaction: scrubTransaction,
    beforeSendLog: scrubLog,
  };
}

export function clientSentryOptions(
  env: SentryRuntimeEnv,
): ClientSentryOptions {
  return {
    ...baseSentryOptions(env),
    tunnel: SENTRY_TUNNEL_ROUTE,
    // Session envelopes bypass beforeSend and can include SDK user identity.
    // Release-health sessions are outside our monitoring scope; retain all
    // other defaults, including Next.js tracing and error integrations.
    integrations: (defaults) => [
      ...defaults.filter((integration) => integration.name !== "BrowserSession"),
      vindorPrivacyIntegration(),
    ],
  };
}

export function serverSentryOptions(
  env: SentryRuntimeEnv,
): ServerSentryOptions & {
  integrations: (defaults: Integration[]) => Integration[];
} {
  return {
    ...baseSentryOptions(env),
    integrations: (defaults) => [...defaults, vindorPrivacyIntegration()],
  };
}

/** Upload only with a complete server-side configuration; never require secrets. */
export function sourceMapUploadEnabled(env: {
  [key: string]: string | undefined;
  SENTRY_AUTH_TOKEN?: string;
  SENTRY_ORG?: string;
  SENTRY_PROJECT?: string;
}): boolean {
  return Boolean(env.SENTRY_AUTH_TOKEN && env.SENTRY_ORG && env.SENTRY_PROJECT);
}
