import type { components } from "@/lib/api/schema";

export function orderStatusLabel(
  order: components["schemas"]["OrderRead"],
): string {
  if (order.status === "draft") return "Draft — stock not reserved";
  switch (order.payment_status) {
    case "pending":
      return "Awaiting sandbox payment";
    case "paid":
      return "Paid — sandbox only";
    case "failed":
      return "Payment failed";
    case "cancelled":
      return "Cancelled — stock released";
    case "expired":
      return "Expired — stock released";
    default:
      return "Placed — unpaid";
  }
}
