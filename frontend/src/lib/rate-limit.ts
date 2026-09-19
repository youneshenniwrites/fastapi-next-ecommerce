// RFC 9110 recipients accept IMF-fixdate and both obsolete HTTP-date forms.
// Normalize first so parsing is UTC and rejects JavaScript's permissive dates.
function httpDate(raw: string, now: number): Date | undefined {
  let canonical = raw;
  const obsolete =
    /^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), (\d{2})-([A-Z][a-z]{2})-(\d{2}) (\d{2}:\d{2}:\d{2}) GMT$/.exec(
      raw,
    );
  const ascii =
    /^(Mon|Tue|Wed|Thu|Fri|Sat|Sun) ([A-Z][a-z]{2}) ( \d|\d{2}) (\d{2}:\d{2}:\d{2}) (\d{4})$/.exec(
      raw,
    );
  if (obsolete) {
    const [, day, date, month, shortYear, time] = obsolete;
    let year =
      Math.floor((new Date(now).getUTCFullYear() + 50) / 100) * 100 +
      Number(shortYear);
    const horizon = new Date(now);
    horizon.setUTCFullYear(horizon.getUTCFullYear() + 50);
    if (Date.parse(`${date} ${month} ${year} ${time} GMT`) > horizon.getTime())
      year -= 100;
    canonical = `${day.slice(0, 3)}, ${date} ${month} ${year} ${time} GMT`;
  } else if (ascii) {
    const [, day, month, date, time, year] = ascii;
    canonical = `${day}, ${date.trim().padStart(2, "0")} ${month} ${year} ${time} GMT`;
  }
  const parsed = new Date(canonical);
  return Number.isFinite(parsed.getTime()) && parsed.toUTCString() === canonical
    ? parsed
    : undefined;
}

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
    const date = httpDate(raw, now);
    if (!date) return undefined;
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
