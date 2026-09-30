"use server";
import * as Sentry from "@sentry/nextjs";
import { headers } from "next/headers";
import { notFound } from "next/navigation";
import { sessionPolicy } from "@/lib/session";
import { requireSentryDiagnosticAdmin } from "@/lib/sentry-diagnostic";

export async function authorizeClientDiagnostic() {
  await requireSentryDiagnosticAdmin();
  const origin = (await headers()).get("origin");
  if (!origin || !sessionPolicy().origins.includes(origin)) notFound();
  return true;
}

export async function captureServerDiagnostic() {
  await authorizeClientDiagnostic();
  Sentry.captureException(
    new Error("Development server observability verification"),
  );
  return { flushed: await Sentry.flush(2000) };
}
