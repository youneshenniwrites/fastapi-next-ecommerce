import { scrubError, scrubTransaction, scrubLog } from "./sentry-privacy";
export const SENTRY_TUNNEL_ROUTE = "/sentry-tunnel";

export interface SentryRuntimeEnv {
  dsn?: string;
  environment?: string;
  nodeEnv?: string;
  tracesSampleRate?: number;
}

interface BaseSentryOptions {
  dsn: string | undefined;
  environment: string;
  tracesSampleRate: number;
  sendDefaultPii: false;
  beforeSend: typeof scrubError;
  beforeSendTransaction: typeof scrubTransaction;
  beforeSendLog: typeof scrubLog;
}

export interface ClientSentryOptions extends BaseSentryOptions {
  tunnel: string;
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
    environment: env.environment || env.nodeEnv || "production",
    tracesSampleRate: sampleRateFor(env),
    sendDefaultPii: false,
    beforeSend: scrubError,
    beforeSendTransaction: scrubTransaction,
    beforeSendLog: scrubLog,
  };
}

export function clientSentryOptions(
  env: SentryRuntimeEnv,
): ClientSentryOptions {
  return { ...baseSentryOptions(env), tunnel: SENTRY_TUNNEL_ROUTE };
}

export function serverSentryOptions(
  env: SentryRuntimeEnv,
): ServerSentryOptions {
  return baseSentryOptions(env);
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
