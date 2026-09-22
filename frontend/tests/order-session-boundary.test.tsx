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
    expect(screen.queryByRole("button", { name: "Private order" })).toBeNull();
  }
  expect(mocks.refresh).toHaveBeenCalled();
});
it("offers account verification recovery without exposing the old order", () => {
  mocks.session.mockReturnValue({ status: "error" });
  render(
    <OrderSessionBoundary owner="a@example.com">
      <button>Private order</button>
    </OrderSessionBoundary>,
  );
  expect(screen.queryByRole("button", { name: "Private order" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Verify account again" }));
  expect(mocks.verify).toHaveBeenCalledTimes(1);
});
it("retry performs a fresh order read instead of navigating to the same cached URL", () => {
  render(<RetryOrders />);
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  expect(mocks.refresh).toHaveBeenCalledTimes(1);
});
it("keeps the same form node through verification so a pending action is not reset", () => {
  mocks.session.mockReturnValue({
    status: "authenticated",
    user: { email: "a@example.com" },
  });
  const view = () => (
    <OrderSessionBoundary owner="a@example.com">
      <input aria-label="Order note" defaultValue="" />
    </OrderSessionBoundary>
  );
  const { rerender } = render(view());
  const input = screen.getByRole("textbox", { name: "Order note" });
  fireEvent.change(input, { target: { value: "in progress" } });
  mocks.session.mockReturnValue({ status: "loading" });
  rerender(view());
  expect(screen.queryByRole("textbox")).toBeNull();
  expect(input.isConnected).toBe(true);
  expect(
    input.closest("[data-order-private]")?.getAttribute("inert"),
  ).not.toBeNull();
  mocks.session.mockReturnValue({
    status: "authenticated",
    user: { email: "a@example.com" },
  });
  rerender(view());
  expect(screen.getByRole("textbox")).toBe(input);
  expect((input as HTMLInputElement).value).toBe("in progress");
});
