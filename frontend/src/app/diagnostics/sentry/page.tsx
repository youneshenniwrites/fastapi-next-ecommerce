import type { Metadata } from "next";
import { requireSentryDiagnosticAdmin } from "@/lib/sentry-diagnostic";
import { SentryDiagnosticControls } from "@/components/sentry-diagnostic-controls";
import { stateLayout } from "@/components/storefront-layout";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { robots: { index: false, follow: false } };

export default async function SentryDiagnosticPage() {
  await requireSentryDiagnosticAdmin();
  return (
    <main id="main" className={stateLayout}>
      <h1>Development monitoring check</h1>
      <p>Send a fixed synthetic error, then confirm receipt in Sentry.</p>
      <SentryDiagnosticControls />
    </main>
  );
}
