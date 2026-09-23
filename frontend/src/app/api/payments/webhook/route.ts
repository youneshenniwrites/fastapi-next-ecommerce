import "server-only";

const MAX_BODY_BYTES = 256 * 1024;
const DEADLINE_MS = 5000;

function reply(status: number) {
  const headers = { "Cache-Control": "no-store" };
  if (status === 204 || status === 205)
    return new Response(null, { status, headers });
  return Response.json(
    status >= 200 && status < 300
      ? { received: true }
      : { error: "Webhook could not be accepted" },
    { status, headers },
  );
}

function backendEndpoint() {
  const raw = process.env.API_BASE_URL;
  if (!raw) throw new Error("Missing API origin");
  const url = new URL(raw);
  const local =
    url.protocol === "http:" &&
    ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname) &&
    process.env.ALLOW_LOCAL_HTTP_SESSIONS === "true";
  if (
    (url.protocol !== "https:" && !local) ||
    url.username ||
    url.password ||
    url.pathname !== "/" ||
    url.search ||
    url.hash
  )
    throw new Error("Invalid API origin");
  return new URL("/api/v1/payments/webhook", url.origin);
}

/** Relay signed bytes to the fixed protected API; FastAPI verifies the signature. */
export async function POST(request: Request) {
  if (process.env.STRIPE_WEBHOOK_RELAY_ENABLED !== "true") return reply(404);
  const signature = request.headers.get("stripe-signature");
  if (!signature?.trim() || signature.length > 2048) return reply(400);
  if (Number(request.headers.get("content-length")) > MAX_BODY_BYTES)
    return reply(413);
  let endpoint: URL;
  try {
    endpoint = backendEndpoint();
  } catch {
    return reply(503);
  }
  const controller = new AbortController();
  const reader = request.body?.getReader();
  let timer: ReturnType<typeof setTimeout> | undefined;
  const deadline = new Promise<never>((_, reject) => {
    timer = setTimeout(() => {
      const error = new DOMException(
        "Webhook deadline exceeded",
        "TimeoutError",
      );
      controller.abort(error);
      reject(error);
    }, DEADLINE_MS);
  });
  try {
    return await Promise.race([
      deadline,
      (async () => {
        const body = new Uint8Array(MAX_BODY_BYTES);
        let total = 0;
        if (reader) {
          while (true) {
            const chunk = await reader.read();
            controller.signal.throwIfAborted();
            if (chunk.done) break;
            if (total + chunk.value.byteLength > MAX_BODY_BYTES)
              return reply(413);
            body.set(chunk.value, total);
            total += chunk.value.byteLength;
          }
        }
        const headers = new Headers({
          "Content-Type": "application/json",
          "Stripe-Signature": signature,
        });
        const bypass = process.env.VERCEL_PROTECTION_BYPASS;
        if (bypass) headers.set("x-vercel-protection-bypass", bypass);
        const upstream = await fetch(endpoint, {
          method: "POST",
          body: body.slice(0, total),
          headers,
          redirect: "error",
          cache: "no-store",
          signal: controller.signal,
        });
        // Never expose upstream bodies, cookies, redirects or infrastructure headers.
        void upstream.body?.cancel().catch(() => {});
        controller.signal.throwIfAborted();
        if (upstream.status >= 300 && upstream.status < 400) return reply(502);
        return reply(upstream.status);
      })(),
    ]);
  } catch {
    return reply(503);
  } finally {
    clearTimeout(timer);
    void reader?.cancel().catch(() => {});
  }
}
