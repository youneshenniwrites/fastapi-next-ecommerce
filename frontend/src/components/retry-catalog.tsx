"use client";
import { useRouter } from "next/navigation";
import { useTransition } from "react";
export function RetryCatalog() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  return (
    <button
      className="button"
      disabled={pending}
      onClick={() => startTransition(() => router.refresh())}
    >
      {pending ? "Trying again…" : "Try again"}
    </button>
  );
}
