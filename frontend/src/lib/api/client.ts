import "server-only";
import createClient from "openapi-fetch";
import type { paths, components } from "./schema";
export type Product = components["schemas"]["ProductRead"];
export function apiClient() {
  return createClient<paths>({
    baseUrl: process.env.API_BASE_URL ?? "http://127.0.0.1:8000",
    cache: "no-store",
    fetch: (request) => fetch(request, { signal: AbortSignal.timeout(5000) }),
  });
}
