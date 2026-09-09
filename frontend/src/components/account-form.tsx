"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, CheckCircle2, LoaderCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function AccountForm({ mode }: { mode: "login" | "register" }) {
  const registering = mode === "register";
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [registered, setRegistered] = useState(false);
  const feedback = useRef<HTMLParagraphElement>(null);
  const busy = useRef(false);
  useEffect(() => {
    if (error || registered) feedback.current?.focus();
  }, [error, registered]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy.current) return;
    busy.current = true;
    setPending(true);
    setError("");
    const form = event.currentTarget;
    const fields = new FormData(form);
    try {
      const response = await fetch(`/api/session/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: String(fields.get("email") ?? "").trim(),
          password: String(fields.get("password") ?? ""),
        }),
        signal: AbortSignal.timeout(10000),
      });
      const result = await response.json();
      if (
        response.ok &&
        (registering
          ? result.registered === true
          : result.authenticated === true)
      ) {
        form.reset();
        if (registering) setRegistered(true);
        else {
          router.replace("/#collection");
          router.refresh();
        }
      } else if (!registering && response.status === 401) {
        setError("Email or password is incorrect. Please try again.");
      } else if (registering && response.status === 400) {
        setError(
          "Unable to create this account. Try signing in or use another email.",
        );
      } else if (response.status === 422) {
        setError("Check your email and password and try again.");
      } else {
        setError(
          registering
            ? "We couldn't confirm registration. Try signing in before registering again."
            : "Sign-in is temporarily unavailable. Please try again.",
        );
      }
    } catch {
      setError(
        registering
          ? "We couldn't confirm registration. Check your connection and try signing in."
          : "We couldn't connect. Check your connection and try again.",
      );
    } finally {
      busy.current = false;
      setPending(false);
    }
  }

  return (
    <main id="main" className="mx-auto w-full max-w-lg px-6 py-12 sm:py-20">
      <Link
        href="/#collection"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground underline-offset-4 hover:underline"
      >
        <ArrowLeft className="size-4" aria-hidden="true" /> Back to the
        collection
      </Link>
      <p className="mt-10 text-xs tracking-widest text-muted-foreground">
        YOUR VINDOR ACCOUNT
      </p>
      <h1 className="mt-3 font-serif text-4xl sm:text-5xl">
        {registering ? "Make yourself at home." : "Welcome back."}
      </h1>
      <p className="mt-4 text-sm leading-6 text-muted-foreground">
        {registering
          ? "Create an account for your workspace collection."
          : "Sign in to your VINDOR account."}{" "}
        This is a portfolio demo. Please use fictional details.
      </p>
      {registered ? (
        <div className="mt-8 rounded-lg border border-border bg-muted p-6">
          <CheckCircle2
            className="mb-3 size-6 text-primary"
            aria-hidden="true"
          />
          <p ref={feedback} tabIndex={-1} role="status" className="text-sm">
            Your account is ready. Sign in to continue.
          </p>
          <Button asChild className="mt-5">
            <Link href="/login">Continue to sign in</Link>
          </Button>
        </div>
      ) : (
        <form
          onSubmit={submit}
          aria-label={registering ? "Create account" : "Sign in"}
          aria-busy={pending}
          className="mt-8 space-y-5"
        >
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              Email address
            </label>
            <Input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              maxLength={254}
              disabled={pending}
              className="h-12"
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">
              Password
            </label>
            <Input
              id="password"
              name="password"
              type="password"
              autoComplete={registering ? "new-password" : "current-password"}
              required
              minLength={registering ? 8 : 1}
              maxLength={registering ? 128 : 1024}
              aria-describedby={registering ? "password-help" : undefined}
              disabled={pending}
              className="h-12"
            />
            {registering && (
              <p id="password-help" className="text-xs text-muted-foreground">
                Use 8–128 characters. Don't reuse a real password.
              </p>
            )}
          </div>
          {error && (
            <p
              ref={feedback}
              role="alert"
              tabIndex={-1}
              className="rounded-md border border-destructive p-3 text-sm text-destructive"
            >
              {error}
            </p>
          )}
          <Button type="submit" disabled={pending} className="h-12 w-full">
            {pending && (
              <LoaderCircle
                className="size-4 animate-spin motion-reduce:animate-none"
                aria-hidden="true"
              />
            )}
            {pending
              ? registering
                ? "Creating account…"
                : "Signing in…"
              : registering
                ? "Create account"
                : "Sign in"}
          </Button>
          <p role="status" className="sr-only">
            {pending ? "Please wait while your request is processed." : ""}
          </p>
        </form>
      )}
      {!registered && (
        <p className="mt-6 text-center text-sm text-muted-foreground">
          {registering ? "Already have an account?" : "New to VINDOR?"}{" "}
          <Link
            href={registering ? "/login" : "/register"}
            className="font-medium text-foreground underline underline-offset-4"
          >
            {registering ? "Sign in" : "Create an account"}
          </Link>
        </p>
      )}
    </main>
  );
}
