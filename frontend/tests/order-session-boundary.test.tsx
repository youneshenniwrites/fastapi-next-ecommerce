// @vitest-environment jsdom
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
const mocks = vi.hoisted(() => ({
  session: vi.fn(),
  refresh: vi.fn(),
  verify: vi.fn(),
}));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: mocks.refresh }),
}));
vi.mock("@/components/session-provider", () => ({
  useSession: mocks.session,
  useSessionRefresh: () => mocks.verify,
}));
import { OrderSessionBoundary } from "../src/components/order-session-boundary";
import { RetryOrders } from "../src/components/retry-orders";
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
it("conceals old order snapshots during account resolution and account switches", () => {
  mocks.session.mockReturnValue({
    status: "authenticated",
    user: { email: "a@example.com" },
  });
  const view = () => (
    <OrderSessionBoundary owner="a@example.com">
      <button>Private order</button>
    </OrderSessionBoundary>
  );
  const { rerender } = render(view());
  expect(screen.queryByText("Private order")).not.toBeNull();
  for (const session of [
    { status: "loading" },
    { status: "guest" },
    { status: "authenticated", user: { email: "b@example.com" } },
  ]) {
    mocks.session.mockReturnValue(session);
    rerender(view());
    expect(screen.queryByText("Private order")).toBeNull();
  }
  expect(mocks.refresh).toHaveBeenCalled();
});
it("offers account verification recovery without exposing the old order", () => {
  mocks.session.mockReturnValue({ status: "error" });
  render(
    <OrderSessionBoundary owner="a@example.com">
      Private order
    </OrderSessionBoundary>,
  );
  expect(screen.queryByText("Private order")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Verify account again" }));
  expect(mocks.verify).toHaveBeenCalledTimes(1);
});
it("retry performs a fresh order read instead of navigating to the same cached URL", () => {
  render(<RetryOrders />);
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  expect(mocks.refresh).toHaveBeenCalledTimes(1);
});
