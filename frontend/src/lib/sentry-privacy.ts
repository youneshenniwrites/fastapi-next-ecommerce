import {
  spanToJSON,
  type ErrorEvent,
  type Log,
  type Span,
  type StreamedSpanJSON,
  type TransactionEvent,
} from "@sentry/core";

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
const httpMethods = new Set([
  "GET",
  "HEAD",
  "POST",
  "PUT",
  "DELETE",
  "CONNECT",
  "OPTIONS",
  "TRACE",
  "PATCH",
]);
function httpMethod(value: unknown): string | undefined {
  if (
    typeof value !== "string" ||
    !/^[!#$%&'*+.^_`|~0-9A-Za-z-]+(?![\s\S])/.test(value)
  )
    return;
  return httpMethods.has(value) ? value : "_OTHER";
}
function httpData(value: unknown): RecordValue {
  const data = record(record(value).data);
  const result: RecordValue = {};
  for (const key of ["http.method", "http.request.method"]) {
    const method = httpMethod(data[key]);
    if (method !== undefined) result[key] = method;
  }
  for (const key of ["http.response.status_code", "http.status_code"]) {
    const status = data[key];
    if (
      typeof status === "number" &&
      Number.isInteger(status) &&
      status >= 100 &&
      status <= 599
    )
      result[key] = status;
  }
  return result;
}
function operationLabel(value: unknown, data: RecordValue = {}): string {
  const label =
    typeof value === "string" && Object.hasOwn(operationLabels, value)
      ? operationLabels[value]
      : "Application operation";
  const method = data["http.request.method"] ?? data["http.method"];
  return (value === "http.server" || value === "http.client") && method
    ? `${method} · ${label}`
    : label;
}
function traceStructure(value: unknown, fields = traceFields): RecordValue {
  const result = pick(value, fields);
  const op = record(value).op;
  if (op !== undefined)
    result.op =
      typeof op === "string" && Object.hasOwn(operationLabels, op)
        ? op
        : "app.operation";
  const data = httpData(value);
  if (Object.keys(data).length) result.data = data;
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
        ? operationLabel(
            record(record(event.contexts).trace).op,
            httpData(record(event.contexts).trace),
          )
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
      description: operationLabel(record(span).op, httpData(span)),
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
const labelValues = new Set(Object.values(operationLabels));
const segmentSources = new Set([
  "custom",
  "url",
  "route",
  "view",
  "component",
  "task",
]);

function attributeValue(value: unknown): unknown {
  return value !== null &&
    typeof value === "object" &&
    !Array.isArray(value) &&
    "value" in value
    ? (value as { value: unknown }).value
    : value;
}

function flatAttributes(value: unknown): RecordValue {
  return Object.fromEntries(
    Object.entries(record(value)).map(([key, item]) => [
      key,
      attributeValue(item),
    ]),
  );
}

function knownOperationLabel(value: unknown): string | undefined {
  if (typeof value !== "string") return;
  if (labelValues.has(value)) return value;
  const match = /^((?:[A-Z]+)|_OTHER) · (.+)$/.exec(value);
  if (!match || !labelValues.has(match[2])) return;
  if (match[1] !== "_OTHER" && !httpMethods.has(match[1])) return;
  return value;
}

function hexId(value: unknown, length: number): string | undefined {
  return typeof value === "string" &&
    new RegExp(`^[0-9a-f]{${length}}$`).test(value)
    ? value
    : undefined;
}

function seconds(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function plain(value: unknown): string | undefined {
  return typeof value === "string" && /^[\w.@+:/-]{1,80}$/.test(value)
    ? value
    : undefined;
}

/** Envelope trace headers copy the raw span name. Replace that with the operation label. */
export function samplingTransactionLabel(span: unknown): string {
  if (!span || typeof span !== "object") return "Application operation";
  const flat = flatAttributes(
    "attributes" in span ? (span as { attributes?: unknown }).attributes : span,
  );
  return operationLabel(flat["sentry.op"], httpData({ data: flat }));
}

export function scrubSamplingTransaction(
  transaction: string | undefined,
  span: unknown,
): string | undefined {
  if (typeof transaction !== "string") return transaction;
  try {
    return samplingTransactionLabel(span ? spanToJSON(span as Span) : undefined);
  } catch {
    return "Application operation";
  }
}

/** Sentry 11 streams spans outside beforeSendTransaction. Keep the same allowlist. */
export function scrubStreamedSpan(span: StreamedSpanJSON): StreamedSpanJSON {
  const flat = flatAttributes(span.attributes);
  const http = httpData({ data: flat });
  const label = operationLabel(flat["sentry.op"], http);
  const attributes: RecordValue = {
    "sentry.op":
      typeof flat["sentry.op"] === "string" &&
      Object.hasOwn(operationLabels, flat["sentry.op"])
        ? flat["sentry.op"]
        : "app.operation",
    "sentry.segment.name": span.is_segment
      ? label
      : (knownOperationLabel(flat["sentry.segment.name"]) ??
        "Application operation"),
    ...http,
  };
  const origin = plain(flat["sentry.origin"]);
  if (origin && /^[a-z]+(?:\.[a-z0-9]+){0,5}$/i.test(origin))
    attributes["sentry.origin"] = origin;
  const segmentId = hexId(flat["sentry.segment.id"], 16);
  if (segmentId) attributes["sentry.segment.id"] = segmentId;
  if (
    flat["sentry.trace_lifecycle"] === "stream" ||
    flat["sentry.trace_lifecycle"] === "static"
  )
    attributes["sentry.trace_lifecycle"] = flat["sentry.trace_lifecycle"];
  for (const key of [
    "sentry.sdk.name",
    "sentry.sdk.version",
    "sentry.release",
    "sentry.environment",
  ]) {
    const item = plain(flat[key]);
    if (item) attributes[key] = item;
  }
  const sample = flat["sentry.sample_rate"];
  if (typeof sample === "number" && sample >= 0 && sample <= 1)
    attributes["sentry.sample_rate"] = sample;
  if (
    typeof flat["sentry.segment.name.source"] === "string" &&
    segmentSources.has(flat["sentry.segment.name.source"])
  )
    attributes["sentry.segment.name.source"] =
      flat["sentry.segment.name.source"];
  const parent = hexId(span.parent_span_id, 16);
  const end = seconds(span.end_timestamp);
  return {
    name: label,
    span_id: hexId(span.span_id, 16) ?? "0".repeat(16),
    trace_id: hexId(span.trace_id, 32) ?? "0".repeat(32),
    ...(parent ? { parent_span_id: parent } : {}),
    start_timestamp: seconds(span.start_timestamp) ?? 0,
    ...(end !== undefined ? { end_timestamp: end } : {}),
    status: span.status === "error" ? "error" : "ok",
    is_segment: span.is_segment === true,
    attributes: attributes as StreamedSpanJSON["attributes"],
  };
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
