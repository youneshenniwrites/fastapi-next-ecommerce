"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useSessionRefresh, useSession } from "@/components/session-provider";

export function OrderSessionBoundary({
  owner,
  children,
}: {
  owner: string;
  children: ReactNode;
}) {
  const session = useSession();
  const refreshSession = useSessionRefresh();
  const router = useRouter();
  const mismatch =
    session.status === "guest" ||
    (session.status === "authenticated" && session.user.email !== owner);
  useEffect(() => {
    if (mismatch) router.refresh();
  }, [mismatch, router]);
  if (session.status === "error")
    return (
      <div>
        <p role="alert">Your account is temporarily unavailable.</p>
        <Button onClick={refreshSession}>Verify account again</Button>
      </div>
    );
  if (session.status !== "authenticated" || session.user.email !== owner)
    return (
      <p role="status">
        Verifying your account before showing private order details…
      </p>
    );
  return children;
}
