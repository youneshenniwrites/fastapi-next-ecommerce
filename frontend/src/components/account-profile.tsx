"use client";
import Link from "next/link";
import { useRef, useState } from "react";
import { LogOut, UserRound } from "lucide-react";
import { useSession } from "@/components/session-provider";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
export function AccountProfile() {
  const session = useSession();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const busy = useRef(false);
  async function signOut() {
    if (busy.current) return;
    busy.current = true;
    setPending(true);
    setError("");
    try {
      const response = await fetch("/api/session/logout", {
        method: "POST",
        signal: AbortSignal.timeout(10000),
      });
      if (!response.ok || (await response.json()).authenticated !== false)
        throw new Error();
      // A full navigation discards in-memory private state and the router cache.
      window.location.replace("/login");
    } catch {
      setError("We couldn't confirm sign-out. Please try again.");
      setPending(false);
      busy.current = false;
    }
  }
  return (
    <main id="main" className="mx-auto w-full max-w-xl px-6 py-12 sm:py-20">
      <p className="text-xs tracking-widest text-muted-foreground">
        YOUR VINDOR ACCOUNT
      </p>
      <h1 className="mt-3 font-serif text-4xl sm:text-5xl">Your space.</h1>
      {session.status === "loading" ? (
        <div role="status" className="mt-8 space-y-4">
          <span className="sr-only">Loading your account…</span>
          <Skeleton className="h-8 w-2/3" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : session.status === "guest" ? (
        <section className="mt-8 space-y-5">
          <h2 className="text-xl">Sign in to view your account</h2>
          <p className="text-sm text-muted-foreground">
            Your session may have expired. Sign in to continue.
          </p>
          <Button asChild>
            <Link href="/login" prefetch={false}>
              Sign in
            </Link>
          </Button>
        </section>
      ) : session.status === "error" ? (
        <section className="mt-8 space-y-5">
          <p role="alert">
            Your account is temporarily unavailable. Please try again.
          </p>
          <Button onClick={() => window.location.reload()}>Try again</Button>
        </section>
      ) : (
        <section
          aria-label="Customer profile"
          className="mt-8 rounded-lg border border-border p-6 sm:p-8"
        >
          <UserRound aria-hidden="true" className="mb-5 size-7 text-primary" />
          <h2 className="text-xl">Account details</h2>
          <dl className="mt-6 space-y-5 text-sm">
            <div>
              <dt className="text-muted-foreground">Email address</dt>
              <dd className="mt-1 break-all font-medium">
                {session.user.email}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Member since</dt>
              <dd className="mt-1">
                {new Intl.DateTimeFormat("en-GB", {
                  dateStyle: "long",
                  timeZone: "UTC",
                }).format(new Date(session.user.created_at))}
              </dd>
            </div>
          </dl>
          <Button onClick={signOut} disabled={pending} className="mt-8">
            <LogOut aria-hidden="true" />
            {pending ? "Signing out…" : "Sign out"}
          </Button>
          {error && (
            <p role="alert" className="mt-4 text-sm text-destructive">
              {error}
            </p>
          )}
        </section>
      )}
      <p className="mt-8 text-sm text-muted-foreground">
        A fictional shop. Browse the collection in GBP.
      </p>
      {/* Full navigation intentionally discards the private account router state. */}
      {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
      <a
        href="/#collection"
        className="mt-3 inline-block text-sm underline underline-offset-4"
      >
        Back to the collection
      </a>
    </main>
  );
}
