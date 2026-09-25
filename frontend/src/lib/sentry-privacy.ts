import type { ErrorEvent, TransactionEvent, Log } from "@sentry/core";

export const FILTERED = "[Filtered]";
type RecordValue = Record<string, unknown>;
function record(value: unknown): RecordValue {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as RecordValue)
    : {};
}
function pick(value: unknown, fields: string[]): RecordValue {
  return Object.fromEntries(
    Object.entries(record(value)).filter(
      ([key, item]) =>
        fields.includes(key) &&
        ["string", "number", "boolean"].includes(typeof item),
    ),
  );
}
function filename(value: unknown): string | undefined {
  if (typeof value !== "string") return;
  let path = value.split(/[?#]/)[0].replaceAll("\\", "/");
  // Retain Next artifact paths for source maps without hosts, credentials or queries.
  const next = path.indexOf("/_next/static/");
  path = next >= 0 ? path.slice(next) : path.split("/").at(-1)!;
  return /^[A-Za-z0-9_./-]+\.(py|js|mjs|cjs|ts|tsx|jsx)$/.test(path)
    ? path
    : undefined;
}
function frames(value: unknown) {
  const items = record(value).frames;
  return {
    frames: Array.isArray(items)
      ? items.map((value) => {
          const frame = record(value);
          const clean = pick(frame, ["lineno", "colno", "in_app"]);
          const file = filename(frame.filename);
          if (file) clean.filename = file;
          for (const key of ["function", "module"]) {
            const item = frame[key];
            if (
              typeof item === "string" &&
              /^[A-Za-z_][A-Za-z0-9_.<>-]{0,120}$/.test(item)
            )
              clean[key] = item;
          }
          return clean;
        })
      : [],
  };
}
const debugId =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const traceFields = [
  "trace_id",
  "span_id",
  "parent_span_id",
  "op",
  "status",
  "origin",
];
function structure(event: RecordValue): RecordValue {
  const result = pick(event, [
    "event_id",
    "type",
    "level",
    "platform",
    "timestamp",
    "start_timestamp",
    "release",
    "environment",
  ]);
  for (const key of ["message", "transaction"])
    if (key in event) result[key] = FILTERED;
  const values = record(event.exception).values;
  if (Array.isArray(values))
    result.exception = {
      values: values.map((value) => ({
        ...pick(value, ["type", "module"]),
        value: FILTERED,
        stacktrace: frames(record(value).stacktrace),
      })),
    };
  if (event.contexts)
    result.contexts = {
      trace: pick(record(event.contexts).trace, traceFields),
    };
  if (Array.isArray(event.spans))
    result.spans = event.spans.map((span) => ({
      ...pick(span, [...traceFields, "timestamp", "start_timestamp"]),
      description: FILTERED,
    }));
  const images = record(event.debug_meta).images;
  if (Array.isArray(images)) {
    result.debug_meta = {
      images: images.flatMap((value) => {
        const image = record(value);
        const file = filename(image.code_file);
        return image.type === "sourcemap" &&
          typeof image.debug_id === "string" &&
          debugId.test(image.debug_id) &&
          file
          ? [{ type: "sourcemap", debug_id: image.debug_id, code_file: file }]
          : [];
      }),
    };
  }
  return result;
}
/** Arbitrary request, breadcrumb and application context is deliberately discarded. */
export function scrubError(event: ErrorEvent): ErrorEvent {
  return structure(event as unknown as RecordValue) as unknown as ErrorEvent;
}
export function scrubTransaction(event: TransactionEvent): TransactionEvent {
  return structure(
    event as unknown as RecordValue,
  ) as unknown as TransactionEvent;
}
/** Logs remain disabled; the defensive hook retains only SDK correlation metadata. */
export function scrubLog(log: Log): Log {
  return {
    ...log,
    message: FILTERED,
    attributes: pick(log.attributes, [
      "sentry.release",
      "sentry.environment",
    ]) as Log["attributes"],
  };
}
