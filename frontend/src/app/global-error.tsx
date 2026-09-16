"use client";
import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";
import { stateLayout } from "@/components/storefront-layout";
import { Button } from "@/components/ui/button";
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);
  return (
    <html lang="en">
      <body>
        <main id="main" className={stateLayout}>
          <h1>Something interrupted the moment.</h1>
          <p>We couldn’t load this page. Please try again.</p>
          <Button onClick={reset}>Try again</Button>
        </main>
      </body>
    </html>
  );
}
