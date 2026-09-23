import { RetryOrders } from "@/components/retry-orders";
import { OrderSessionBoundary } from "@/components/order-session-boundary";
import Link from "next/link";
import { readOrders } from "@/lib/order-data";
import { money } from "@/lib/catalog";
import { orderStatusLabel } from "@/lib/order-status";

export const metadata = {
  title: "Order history",
  robots: { index: false, follow: false },
};
export default async function OrdersPage({
  searchParams,
}: {
  searchParams: Promise<{ after?: string }>;
}) {
  const { after } = await searchParams;
  const cursor = after && /^\d+$/.test(after) ? Number(after) : 0;
  const result = await readOrders(Number.isSafeInteger(cursor) ? cursor : 0);
  return (
    <main id="main" className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="font-serif text-4xl">Your orders</h1>
      {result.status === "ready" ? (
        <OrderSessionBoundary owner={result.owner}>
          {!result.data.length && (
            <p className="mt-6">No orders on this page yet.</p>
          )}
          <ul className="my-6 divide-y">
            {result.data.slice(0, 20).map((order) => (
              <li key={order.id} className="py-4">
                <Link href={`/orders/${order.id}`} prefetch={false}>
                  Order #{order.id} — {orderStatusLabel(order)} —{" "}
                  {money(order.total)} GBP
                </Link>
              </li>
            ))}
          </ul>
          {result.data.length > 20 && (
            <Link href={`/orders?after=${result.data[19].id}`} prefetch={false}>
              More orders
            </Link>
          )}
        </OrderSessionBoundary>
      ) : (
        <p className="mt-6">
          {result.status === "guest" ? (
            <Link href="/login">Sign in to view your orders</Link>
          ) : (
            <>
              Orders unavailable. <RetryOrders />
            </>
          )}
        </p>
      )}
      <p className="mt-8">
        <Link href="/cart" prefetch={false}>
          Back to your cart
        </Link>
      </p>
    </main>
  );
}
