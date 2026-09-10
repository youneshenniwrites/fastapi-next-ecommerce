"use client";
import Link from "next/link";
import { useSession } from "@/components/session-provider";
export function AccountLink({
  className,
  onClick,
}: {
  className?: string;
  onClick?: () => void;
}) {
  const session = useSession();
  if (session.status === "loading") {
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
