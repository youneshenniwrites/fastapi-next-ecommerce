import "server-only";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import { apiClient } from "./api/client";
import { sessionPolicy } from "./session";

/** Resolve privileges through FastAPI on every request, never browser claims. */
export async function requireSentryDiagnosticAdmin() {
  if (
    process.env.SENTRY_DIAGNOSTICS_ENABLED !== "true" ||
    process.env.SENTRY_ENVIRONMENT !== "development"
  )
    notFound();
  const token = (await cookies()).get(sessionPolicy().name)?.value;
  if (!token) notFound();
  const result = await apiClient().GET("/api/v1/auth/me", {
    redirect: "error",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (
    result.response.status !== 200 ||
    result.data?.is_active !== true ||
    result.data?.is_superuser !== true
  )
    notFound();
}
