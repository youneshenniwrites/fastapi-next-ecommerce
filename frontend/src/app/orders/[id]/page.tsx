import { RetryOrders } from "@/components/retry-orders";
import { OrderSessionBoundary } from "@/components/order-session-boundary";
import Link from "next/link";
import { readOrder } from "@/lib/order-data";
import { money } from "@/lib/catalog";
import { CheckoutSubmit } from "@/components/checkout-submit";
import { placeCheckout } from "../actions";
import {
  startPayment,
  cancelPayment,
  reconcilePayment,
} from "../payment-actions";
import { orderStatusLabel } from "@/lib/order-status";

export const metadata = {
  title: "Your order",
  robots: { index: false, follow: false },
};
export default async function OrderPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const result = await readOrder(/^\d+$/.test(id) ? Number(id) : NaN);
  return (
    <main id="main" className="mx-auto max-w-3xl px-6 py-12">
      {result.status !== "ready" ? (
        <>
          <h1 className="text-3xl">Order unavailable</h1>
          <p>
            {result.status === "guest"
              ? "Sign in to view your order."
              : result.status === "missing"
                ? "We couldn't find this order in your account."
                : "Your order is temporarily unavailable. Please try again."}
          </p>
          {result.status === "guest" ? (
            <Link href="/login">Sign in</Link>
          ) : (
            <RetryOrders />
          )}
        </>
      ) : (
        <OrderSessionBoundary owner={result.owner}>
          <h1 className="font-serif text-4xl">
            {result.data.payment_status
              ? "Your demo order"
              : result.data.status === "placed"
                ? "Order confirmed"
                : "Review your order"}
          </h1>
          <p className="mt-4">
            Order #{result.data.id} · {orderStatusLabel(result.data)}
          </p>
          <ul className="my-6 divide-y">
            {result.data.lines.map((line) => (
              <li key={line.product_id} className="py-4">
                {line.product_name} × {line.quantity}
                <span className="float-right">{money(line.line_total)}</span>
              </li>
            ))}
          </ul>
          <p className="text-xl font-semibold">
            Total: {money(result.data.total)} GBP
          </p>
          <p className="mt-4">
            Fictional demo. No real money is collected and no goods will be
            shipped.
          </p>
          {result.data.payment_status === "pending" && (
            <section aria-label="Sandbox payment" className="mt-6">
              <p>
                Use Stripe test card details only. Returning from Stripe does
                not confirm payment; check the status below.
              </p>
              {result.data.payment_expires_at && (
                <p>
                  Payment deadline:{" "}
                  {new Date(result.data.payment_expires_at).toUTCString()}.
                </p>
              )}
              <CheckoutSubmit
                action={startPayment.bind(null, result.owner, result.data.id)}
                owner={result.owner}
                label="Pay with Stripe sandbox"
              />
              <CheckoutSubmit
                action={reconcilePayment.bind(
                  null,
                  result.owner,
                  result.data.id,
                )}
                owner={result.owner}
                label="Check payment status"
              />
              <p className="mt-6">
                Cancel this unpaid order to release its stock. A processing
                payment must finish before its stock can be released. Items are
                not added back to your cart.
              </p>
              <CheckoutSubmit
                action={cancelPayment.bind(null, result.owner, result.data.id)}
                owner={result.owner}
                label="Cancel unpaid order"
              />
            </section>
          )}
          {result.data.payment_status === "paid" && (
            <p className="mt-4" role="status">
              Sandbox payment confirmed by the server. Thank you for trying
              VINDOR.
            </p>
          )}
          {result.data.status === "draft" && (
            <CheckoutSubmit
              action={placeCheckout.bind(null, result.owner, result.data.id)}
              owner={result.owner}
              label="Place demo order"
            />
          )}
        </OrderSessionBoundary>
      )}
      <nav className="mt-8 flex gap-6" aria-label="Order navigation">
        <Link href="/cart" prefetch={false}>
          Your cart
        </Link>
        <Link href="/orders" prefetch={false}>
          Order history
        </Link>
      </nav>
    </main>
  );
}
