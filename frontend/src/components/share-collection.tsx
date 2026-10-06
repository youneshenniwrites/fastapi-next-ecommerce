"use client";
import { useEffect, useRef, useState } from "react";
import { Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/**
 * Remount with `key={href}` when the selection changes: a clipboard write that
 * finishes late then belongs to an unmounted component and cannot announce
 * that the current selection was copied.
 */
export function ShareCollection({ href }: { href: string }) {
  const [message, setMessage] = useState("");
  const [fallback, setFallback] = useState("");
  const [copying, setCopying] = useState(false);
  const active = useRef(false);
  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
    };
  }, []);

  async function share() {
    const url = `${window.location.origin}${href}`;
    setCopying(true);
    setMessage("");
    try {
      await navigator.clipboard.writeText(url);
      if (!active.current) return;
      setFallback("");
      setMessage("Collection link copied.");
    } catch {
      if (!active.current) return;
      setFallback(url);
      setMessage("Couldn’t copy automatically. Copy the link below.");
    } finally {
      if (active.current) setCopying(false);
    }
  }

  return (
    <div className="flex min-w-0 flex-col items-start gap-2 sm:items-end">
      <Button
        variant="outline"
        size="lg"
        className="min-h-11"
        onClick={share}
        disabled={copying}
      >
        <Share2 aria-hidden="true" /> Share results
      </Button>
      <p aria-live="polite" className="text-xs text-muted-foreground">
        {message}
      </p>
      {fallback && (
        <Input
          aria-label="Collection link"
          value={fallback}
          readOnly
          autoFocus
          onFocus={(event) => event.currentTarget.select()}
          className="w-full sm:w-80"
        />
      )}
    </div>
  );
}
