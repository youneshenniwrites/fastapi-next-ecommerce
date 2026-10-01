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
  "status",
  "origin",
];
// Descriptions are derived only from a finite SDK operation vocabulary. Never
// copy names, URLs, route parameters, SQL or request-derived span attributes.
const operationLabels: Record<string, string> = {
  "http.server": "Storefront request",
  "http.client": "API request",
  "http.server.middleware": "Request middleware",
  "function.nextjs": "Next.js function",
  "function.nextjs.server_component": "Server component",
  "function.nextjs.server_action": "Server action",
  "ui.nextjs": "Page render",
  "ui.render": "Component render",
  pageload: "Page load",
  navigation: "Page navigation",
  "resource.script": "Script load",
  "resource.css": "Stylesheet load",
  "resource.img": "Image load",
  browser: "Browser operation",
};
function operationLabel(value: unknown): string {
  return typeof value === "string" && Object.hasOwn(operationLabels, value)
    ? operationLabels[value]
    : "Application operation";
}
function traceStructure(value: unknown, fields = traceFields): RecordValue {
  const result = pick(value, fields);
  const op = record(value).op;
  if (op !== undefined)
    result.op =
      typeof op === "string" && Object.hasOwn(operationLabels, op)
        ? op
        : "app.operation";
  return result;
}
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
  if ("message" in event) result.message = FILTERED;
  if ("transaction" in event)
    result.transaction =
      event.type === "transaction"
        ? operationLabel(record(record(event.contexts).trace).op)
        : FILTERED;
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
      trace: traceStructure(record(event.contexts).trace),
    };
  if (Array.isArray(event.spans))
    result.spans = event.spans.map((span) => ({
      ...traceStructure(span, [...traceFields, "timestamp", "start_timestamp"]),
      description: operationLabel(record(span).op),
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
