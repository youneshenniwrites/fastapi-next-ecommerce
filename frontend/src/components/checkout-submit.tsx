"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/button";
import type { CheckoutResult } from "@/app/orders/actions";

export function CheckoutSubmit({
  action,
  label,
}: {
  action: (previous: CheckoutResult, form: FormData) => Promise<CheckoutResult>;
  label: string;
}) {
  const [state, submit, pending] = useActionState(
    async (previous: CheckoutResult, form: FormData) => {
      try {
        const result = await action(previous, form);
        if (result.location) window.location.assign(result.location);
        return result;
      } catch {
        return {
          error:
            "We lost the response. Check order history or retry this same order before starting another checkout.",
        };
      }
    },
    { error: "" },
  );
  return (
    <form action={submit} className="mt-6 space-y-4">
      <Button type="submit" disabled={pending}>
        {pending ? "Please wait…" : label}
      </Button>
      <p role="status" aria-live="polite">
        {pending ? "Processing your request…" : ""}
      </p>
      {state.error && <p role="alert">{state.error}</p>}
    </form>
  );
}
