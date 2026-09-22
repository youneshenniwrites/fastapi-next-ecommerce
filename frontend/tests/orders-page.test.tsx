// @vitest-environment jsdom
import type { ReactNode } from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

const { readOrders } = vi.hoisted(() => ({ readOrders: vi.fn() }));
vi.mock("@/lib/order-data", () => ({ readOrders }));
vi.mock("@/components/retry-orders", () => ({ RetryOrders: () => null }));
vi.mock("@/components/order-session-boundary", () => ({
  OrderSessionBoundary: ({
    children,
    owner,
  }: {
    children: ReactNode;
    owner: string;
  }) => (
    <section aria-label={`Orders belonging to ${owner}`}>{children}</section>
  ),
}));
import OrdersPage from "../src/app/orders/page";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

for (const count of [20, 21])
  it(`renders twenty orders and only offers another page with lookahead (${count})`, async () => {
    readOrders.mockResolvedValue({
      status: "ready",
      owner: "customer@example.com",
      data: Array.from({ length: count }, (_, index) => ({
        id: 101 + index,
        status: "placed",
        total: "12.00",
      })),
    });
    render(
      await OrdersPage({ searchParams: Promise.resolve({ after: "100" }) }),
    );
    expect(readOrders).toHaveBeenCalledWith(100);
    expect(
      screen.getByRole("region", {
        name: "Orders belonging to customer@example.com",
      }),
    ).toBeTruthy();
    expect(screen.getAllByRole("listitem")).toHaveLength(20);
    expect(
      screen.getByRole("link", { name: /Order #120 / }).getAttribute("href"),
    ).toBe("/orders/120");
    expect(screen.queryByRole("link", { name: /Order #121 / })).toBeNull();
    const more = screen.queryByRole("link", { name: "More orders" });
    if (count === 21)
      expect(more?.getAttribute("href")).toBe("/orders?after=120");
    else expect(more).toBeNull();
  });
