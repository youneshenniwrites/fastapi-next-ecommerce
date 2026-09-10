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
  const guest = session.status === "guest";
  return (
    <Link
      href={guest ? "/login" : "/account"}
      className={className}
      onClick={onClick}
    >
      {guest ? "Sign in" : "My account"}
    </Link>
  );
}
