"use client";
import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { Button } from "@/components/ui/button";
export function RetryOrders() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  return (
    <Button
      disabled={pending}
      onClick={() => startTransition(() => router.refresh())}
    >
      {pending ? "Loading orders…" : "Try again"}
    </Button>
  );
}
