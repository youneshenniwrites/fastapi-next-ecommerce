import { RetryOrders } from "@/components/retry-orders";
import { OrderSessionBoundary } from "@/components/order-session-boundary";
import Link from "next/link";
import { readOrder } from "@/lib/order-data";
import { money } from "@/lib/catalog";
import { CheckoutSubmit } from "@/components/checkout-submit";
import { placeCheckout } from "../actions";

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
            {result.data.status === "placed"
              ? "Order confirmed"
              : "Review your order"}
          </h1>
          <p className="mt-4">
            Order #{result.data.id} ·{" "}
            {result.data.status === "placed"
              ? "Placed — unpaid"
              : "Draft — stock not reserved"}
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
            Fictional demo. No payment is collected and no goods will be
            shipped.
          </p>
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
