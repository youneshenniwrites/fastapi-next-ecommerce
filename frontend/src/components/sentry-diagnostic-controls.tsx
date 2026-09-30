"use client";
import { useState } from "react";
import * as Sentry from "@sentry/nextjs";
import { Button } from "@/components/ui/button";
import {
  authorizeClientDiagnostic,
  captureServerDiagnostic,
} from "@/app/diagnostics/sentry/actions";

export function SentryDiagnosticControls() {
  const [pending, setPending] = useState(false);
  const [status, setStatus] = useState("");
  async function send(runtime: "client" | "server") {
    setPending(true);
    setStatus("");
    try {
      let flushed;
      if (runtime === "client") {
        await authorizeClientDiagnostic();
        Sentry.captureException(
          new Error("Development browser observability verification"),
        );
        flushed = await Sentry.flush(2000);
      } else {
        flushed = (await captureServerDiagnostic()).flushed;
      }
      setStatus(
        flushed
          ? "Event queued and flushed. Confirm receipt in Sentry."
          : "Delivery timed out. Check Sentry before retrying.",
      );
    } catch {
      setStatus(
        "Check unavailable. Verify access and development configuration.",
      );
    } finally {
      setPending(false);
    }
  }
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <Button disabled={pending} onClick={() => void send("client")}>
          Test browser error
        </Button>
        <Button disabled={pending} onClick={() => void send("server")}>
          Test server error
        </Button>
      </div>
      <p role="status">{status}</p>
    </div>
  );
}
