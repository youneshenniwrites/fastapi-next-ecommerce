import "server-only";
import createClient from "openapi-fetch";
import type { paths, components } from "./schema";
export type Product = components["schemas"]["ProductRead"];
export function apiClient() {
  // Server-only bypass for the Vercel-gated development API (never browser-exposed);
  // production leaves it unset and is unaffected.
  const bypass = process.env.VERCEL_PROTECTION_BYPASS;
  return createClient<paths>({
    baseUrl: process.env.API_BASE_URL ?? "http://127.0.0.1:8000",
    cache: "no-store",
    headers: bypass ? { "x-vercel-protection-bypass": bypass } : undefined,
    fetch: (request) => fetch(request, { signal: AbortSignal.timeout(5000) }),
  });
}
