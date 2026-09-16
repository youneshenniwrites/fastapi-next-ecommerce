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
