// Treat upstream timing as untrusted; excessive/malformed delays use generic copy.
export function retryAfterSeconds(
  value: string | null,
  now = Date.now(),
): number | undefined {
  if (value === null) return undefined;
  const raw = value.trim();
  let seconds: number;
  if (/^\d+$/.test(raw)) {
    seconds = Number(raw);
  } else {
    const date = new Date(raw);
    if (!Number.isFinite(date.getTime()) || date.toUTCString() !== raw)
      return undefined;
    seconds = Math.max(0, Math.ceil((date.getTime() - now) / 1000));
  }
  return Number.isSafeInteger(seconds) && seconds <= 86400
    ? seconds
    : undefined;
}

export function rateLimitMessage(seconds?: number): string {
  return seconds === undefined
    ? "Too many requests. Wait briefly, then try again."
    : `Too many requests. Wait ${seconds} ${seconds === 1 ? "second" : "seconds"}, then try again.`;
}
