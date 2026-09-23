// @vitest-environment jsdom
import type { ReactNode } from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
const { readOrder } = vi.hoisted(() => ({ readOrder: vi.fn() }));
vi.mock("@/lib/order-data", () => ({ readOrder }));
vi.mock("@/components/order-session-boundary", () => ({
  OrderSessionBoundary: ({ children }: { children: ReactNode }) => children,
}));
vi.mock("@/components/checkout-submit", () => ({
  CheckoutSubmit: ({ label }: { label: string }) => <button>{label}</button>,
}));
vi.mock("@/app/orders/actions", () => ({ placeCheckout: vi.fn() }));
vi.mock("@/app/orders/payment-actions", () => ({
  startPayment: vi.fn(),
  cancelPayment: vi.fn(),
  reconcilePayment: vi.fn(),
}));
import OrderPage from "../src/app/orders/[id]/page";
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
for (const [payment, label] of [
  [null, "Placed — unpaid"],
  ["pending", "Awaiting sandbox payment"],
  ["paid", "Paid — sandbox only"],
  ["failed", "Payment failed"],
  ["cancelled", "Cancelled — stock released"],
  ["expired", "Expired — stock released"],
] as const) {
  it(`renders authoritative ${payment} state and only offers payment for pending`, async () => {
    readOrder.mockResolvedValue({
      status: "ready",
      owner: "fictional@example.com",
      data: {
        id: 7,
        status: "placed",
        payment_status: payment,
        payment_expires_at: "2026-09-23T20:00:00Z",
        total: "12.00",
        lines: [],
      },
    });
    render(await OrderPage({ params: Promise.resolve({ id: "7" }) }));
    expect(screen.getByText(new RegExp(label))).toBeTruthy();
    const pay = screen.queryByRole("button", {
      name: "Pay with Stripe sandbox",
    });
    if (payment === "pending") {
      expect(pay).toBeTruthy();
      expect(
        screen.getByRole("button", { name: "Check payment status" }),
      ).toBeTruthy();
      expect(
        screen.getByRole("button", { name: "Cancel unpaid order" }),
      ).toBeTruthy();
      expect(
        screen.getByText(/Returning from Stripe does not confirm payment/),
      ).toBeTruthy();
    } else expect(pay).toBeNull();
  });
}
