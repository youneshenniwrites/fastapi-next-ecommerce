"use client";
import Link from "next/link";
import { useSyncExternalStore } from "react";
import { useSession } from "@/components/session-provider";
const subscribe = () => () => {};
export function AccountLink({
  className,
  onClick,
}: {
  className?: string;
  onClick?: () => void;
}) {
  const session = useSession();
  // The session can resolve before this streamed header hydrates. Match its
  // server placeholder first, then render the current session normally.
  const hydrated = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
  if (!hydrated || session.status === "loading") {
    return (
      <span className={className} aria-busy="true">
        Account
      </span>
    );
  }
  if (session.status === "guest")
    return (
      <Link
        href="/login"
        prefetch={false}
        className={className}
        onClick={onClick}
      >
        Sign in
      </Link>
    );
  return (
    <a href="/account" className={className} onClick={onClick}>
      My account
    </a>
  );
}
