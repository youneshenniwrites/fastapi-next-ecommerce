"use client";

import { useEffect, useState, type ReactNode } from "react";
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
  const [activating, setActivating] = useState(false);
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    const finish = () => {
      clearTimeout(timer);
      timer = setTimeout(() => setActivating(false), 0);
    };
    for (const event of ["pointerup", "pointercancel", "blur", "pagehide"])
      window.addEventListener(event, finish);
    return () => {
      clearTimeout(timer);
      for (const event of ["pointerup", "pointercancel", "blur", "pagehide"])
        window.removeEventListener(event, finish);
    };
  }, []);
  const mismatch =
    session.status === "guest" ||
    (session.status === "authenticated" && session.user.email !== owner);
  useEffect(() => {
    if (mismatch) router.refresh();
  }, [mismatch, router]);
  const verified =
    session.status === "authenticated" && session.user.email === owner;
  return (
    <div className="grid">
      {!verified && (
        <div className="pointer-events-none col-start-1 row-start-1 self-start">
          <p role={session.status === "error" ? "alert" : "status"}>
            {session.status === "error"
              ? "Your account is temporarily unavailable."
              : "Verifying your account before showing private order details…"}
          </p>
          {(session.status === "error" || mismatch) && (
            <Button
              className="pointer-events-auto"
              onClick={() => {
                refreshSession();
                router.refresh();
              }}
            >
              Verify account again
            </Button>
          )}
        </div>
      )}
      <div
        key={owner}
        className="col-start-1 row-start-1"
        data-order-private
        style={{ opacity: verified ? 1 : 0 }}
        aria-hidden={!verified || undefined}
        inert={!verified && !activating}
        onPointerDownCapture={(event) => {
          if (event.button === 0) setActivating(true);
        }}
      >
        {mismatch ? null : children}
      </div>
    </div>
  );
}
