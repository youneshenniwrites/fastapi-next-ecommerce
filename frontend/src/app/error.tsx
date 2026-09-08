"use client";
import { Button } from "@/components/ui/button";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <main id="main" className="state">
      <h1>Something interrupted the moment.</h1>
      <p>We couldn’t load this page. Please try again.</p>
      <Button onClick={reset}>Try again</Button>
    </main>
  );
}
