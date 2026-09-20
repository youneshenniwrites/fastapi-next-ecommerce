import "server-only";
import createClient from "openapi-fetch";
import type { paths, components } from "./schema";
export type Product = components["schemas"]["ProductRead"];
/** Create the server-only client with bounded JSON reads and transport-managed writes. */
export function apiClient() {
  // Server-only bypass for the Vercel-gated development API (never browser-exposed);
  // production leaves it unset and is unaffected.
  const bypass = process.env.VERCEL_PROTECTION_BYPASS;
  return createClient<paths>({
    baseUrl: process.env.API_BASE_URL ?? "http://127.0.0.1:8000",
    cache: "no-store",
    headers: bypass ? { "x-vercel-protection-bypass": bypass } : undefined,
    fetch: async (request) => {
      // Do not detach unfinished mutations: a recovery read could precede commit.
      // Preserve write transport behavior until operation-status ordering exists.
      if (request.method !== "GET" && request.method !== "HEAD") {
        return fetch(request, { signal: AbortSignal.timeout(5000) });
      }
      const controller = new AbortController();
      let timer: ReturnType<typeof setTimeout> | undefined;
      let response: Response | undefined;
      let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
      const deadline = new Promise<never>((_, reject) => {
        timer = setTimeout(() => {
          const error = new DOMException(
            "API request timed out",
            "TimeoutError",
          );
          controller.abort(error);
          reject(error);
        }, 5000);
      });
      try {
        return await Promise.race([
          (async () => {
            response = await fetch(request, { signal: controller.signal });
            if (controller.signal.aborted) {
              void Promise.allSettled([response.body?.cancel()]);
              throw controller.signal.reason;
            }
            // These endpoints return bounded JSON, not streaming downloads.
            // Drain a clone under the same deadline so delayed bodies cannot
            // strand openapi-fetch's subsequent parsing. Preserve metadata.
            reader = response.clone().body?.getReader();
            if (reader) {
              while (!(await reader.read()).done) {
                // Drain the clone; openapi-fetch consumes the original body.
              }
            }
            controller.signal.throwIfAborted();
            return response;
          })(),
          deadline,
        ]);
      } finally {
        clearTimeout(timer);
        if (controller.signal.aborted) {
          // Cancel both tee branches, including a transport ignoring abort.
          void Promise.allSettled([reader?.cancel(), response?.body?.cancel()]);
        } else {
          reader?.releaseLock();
        }
      }
    },
  });
}
