"use client";

import { useActionState, useEffect } from "react";
import { useSession } from "@/components/session-provider";
import { Button } from "@/components/ui/button";
import type { CheckoutResult } from "@/app/orders/actions";

export function CheckoutSubmit({
  action,
  label,
  owner,
}: {
  action: (previous: CheckoutResult, form: FormData) => Promise<CheckoutResult>;
  label: string;
  owner: string;
}) {
  const session = useSession();
  const [state, submit, pending] = useActionState(
    async (
      previous: CheckoutResult,
      form: FormData,
    ): Promise<CheckoutResult & { owner?: string }> => {
      try {
        const result = await action(previous, form);
        return { ...result, owner };
      } catch {
        return {
          error:
            "We lost the response. Check order history or retry this same order before starting another checkout.",
        };
      }
    },
    { error: "" } as CheckoutResult & { owner?: string },
  );
  useEffect(() => {
    if (
      state.location &&
      state.owner === owner &&
      session.status === "authenticated" &&
      session.user.email === owner
    )
      window.location.assign(state.location);
  }, [state, owner, session]);
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
