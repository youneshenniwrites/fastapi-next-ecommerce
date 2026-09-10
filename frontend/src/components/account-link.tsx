"use client";
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
  const guest = session.status === "guest";
  return (
    <a
      href={guest ? "/login" : "/account"}
      className={className}
      onClick={onClick}
    >
      {guest ? "Sign in" : "My account"}
    </a>
  );
}
