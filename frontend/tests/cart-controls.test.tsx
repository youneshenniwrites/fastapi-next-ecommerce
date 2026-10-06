// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { AddToCartButton } from "../src/components/add-to-cart-button";
import { CartProvider, useCart } from "../src/components/cart-provider";
import type { Product } from "../src/lib/catalog";
import type { CartActionResult, CartSnapshot } from "../src/lib/cart-state";

const boundary = vi.hoisted(() => ({
  change: vi.fn(),
  refresh: vi.fn(),
  refreshSession: vi.fn(),
  session: { status: "authenticated", user: { email: "cart@example.test" } },
}));
vi.mock("next/navigation", () => {
  const router = { refresh: boundary.refresh };
  return { useRouter: () => router };
});
vi.mock("@/components/session-provider", () => ({
  useSession: () => boundary.session,
  useSessionRefresh: () => boundary.refreshSession,
}));
vi.mock("@/app/cart/actions", () => ({ changeCart: boundary.change }));

const product: Product = {
  id: 7,
  name: "Fictional mat",
  description: "Test",
  price: "12.00",
  currency: "GBP",
  stock: 10,
  category: { slug: "desk-organization", name: "Desk organization" },
};
function ready(owner = "cart@example.test", quantity = 1): CartSnapshot {
  return {
    status: "ready",
    owner,
    cart: {
      currency: "GBP",
      items: quantity
        ? [
            {
              product,
              quantity,
              available: true,
              line_total: `${quantity * 12}.00`,
            },
          ]
        : [],
      subtotal: `${quantity * 12}.00`,
    },
  };
}
function Count() {
  const cart = useCart();
  return <output aria-label="Published quantity">{cart.count}</output>;
}
function view(snapshot: CartSnapshot, compact = false, stock = 10) {
  return (
    <CartProvider snapshot={snapshot}>
      <AddToCartButton product={{ ...product, stock }} compact={compact} />
      <Count />
    </CartProvider>
  );
}
async function clickAdd() {
  const button = screen.getByRole("button", { name: "Add to cart" });
  await act(async () => fireEvent.click(button));
}
beforeEach(() => {
  boundary.change.mockReset();
  boundary.refresh.mockReset();
  boundary.refreshSession.mockReset();
  boundary.session = {
    status: "authenticated",
    user: { email: "cart@example.test" },
  };
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.restoreAllMocks();
});

it("dispatches one add across rapid clicks and waits for the authoritative quantity", async () => {
  let complete!: (result: CartActionResult) => void;
  boundary.change.mockImplementation(
    () =>
      new Promise<CartActionResult>((resolve) => {
        complete = resolve;
      }),
  );
  const rendered = render(view(ready()));
  const add = screen.getByRole("button", { name: "Add to cart" });
  fireEvent.click(add);
  fireEvent.click(add);
  expect(boundary.change).toHaveBeenCalledExactlyOnceWith("cart@example.test", {
    kind: "add",
    productId: 7,
  });
  expect(
    (screen.getByRole("button", { name: "Adding…" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true);
  expect(screen.getByLabelText("Published quantity").textContent).toBe("1");
  await act(async () => complete({ ok: true }));
  expect(screen.getByRole("button", { name: "Saved to cart" })).toBeTruthy();
  expect(
    screen.getByText("Saved.", { exact: false }).getAttribute("role"),
  ).toBe("status");
  // A successful action alone is not an authoritative cart read.
  expect(screen.getByLabelText("Published quantity").textContent).toBe("1");
  rendered.rerender(view(ready("cart@example.test", 2)));
  expect(screen.getByLabelText("Published quantity").textContent).toBe("2");
  expect(boundary.change).toHaveBeenCalledOnce();
});

it("clears transient success after four seconds, replaces its timer on another explicit add and cleans up", async () => {
  vi.useFakeTimers();
  boundary.change.mockResolvedValue({ ok: true });
  const rendered = render(view(ready(), true));
  await clickAdd();
  await act(async () => vi.advanceTimersByTime(2000));
  await act(async () =>
    fireEvent.click(screen.getByRole("button", { name: "Saved to cart" })),
  );
  await act(async () => vi.advanceTimersByTime(2000));
  expect(screen.getByRole("button", { name: "Saved to cart" })).toBeTruthy();
  await act(async () => vi.advanceTimersByTime(2000));
  expect(screen.getByRole("button", { name: "Add to cart" })).toBeTruthy();
  expect(boundary.change).toHaveBeenCalledTimes(2);
  rendered.unmount();
  expect(vi.getTimerCount()).toBe(0);
});

it.each(["transport", "uncertain"])(
  "never replays an %s write and requires a new authoritative snapshot before retry",
  async (failure) => {
    if (failure === "transport")
      boundary.change.mockRejectedValue(new Error("private transport detail"));
    else
      boundary.change.mockResolvedValue({
        ok: false,
        uncertain: true,
        error: "Refresh before retrying.",
      });
    const snapshot = ready();
    const rendered = render(view(snapshot));
    await clickAdd();
    await screen.findByRole("alert");
    expect(screen.queryByText("private transport detail")).toBeNull();
    expect(boundary.refresh).toHaveBeenCalledOnce();
    expect(boundary.change).toHaveBeenCalledOnce();
    expect(
      (screen.getByRole("button", { name: "Add to cart" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    rendered.rerender(view(snapshot));
    expect(
      (screen.getByRole("button", { name: "Add to cart" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    rendered.rerender(view(ready("cart@example.test", 2)));
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
    boundary.change.mockResolvedValue({ ok: true });
    await clickAdd();
    expect(boundary.change).toHaveBeenCalledTimes(2);
  },
);

it.each(["Stock changed.", "Your session changed. Sign in again."])(
  "shows the %s rejection and permits an explicit retry",
  async (error) => {
    boundary.change
      .mockResolvedValueOnce({ ok: false, error })
      .mockResolvedValue({ ok: true });
    render(view(ready()));
    await clickAdd();
    expect((await screen.findByRole("alert")).textContent).toContain(error);
    expect(Boolean(screen.queryByRole("link", { name: "Sign in" }))).toBe(
      error.includes("session"),
    );
    expect(boundary.refresh).not.toHaveBeenCalled();
    await clickAdd();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(boundary.change).toHaveBeenCalledTimes(2);
  },
);

it.each([false, true])(
  "offers guest sign-in, unavailable recovery and loading guards (compact=%s)",
  (compact) => {
    const rendered = render(view({ status: "loading", owner: null }, compact));
    expect(
      (screen.getByRole("button", { name: "Loading…" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    rendered.rerender(view({ status: "guest", owner: null }, compact));
    expect(
      screen.getByRole("link", { name: "Sign in to add" }).getAttribute("href"),
    ).toBe("/login");
    rendered.rerender(view({ status: "error", owner: null }, compact));
    boundary.refreshSession.mockClear();
    boundary.refresh.mockClear();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(boundary.refreshSession).toHaveBeenCalledOnce();
    expect(boundary.refresh).toHaveBeenCalledOnce();
    expect(screen.getByRole("alert").textContent).toContain(
      "temporarily unavailable",
    );
    expect(boundary.change).not.toHaveBeenCalled();
  },
);

it("does not dispatch an out-of-stock add", () => {
  render(view(ready(), false, 0));
  const button = screen.getByRole("button", { name: "Out of stock" });
  expect((button as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(button);
  expect(
    screen.getByText("This object is currently out of stock."),
  ).toBeTruthy();
  expect(boundary.change).not.toHaveBeenCalled();
});

it("resets success and hides private controls when the verified account changes", async () => {
  boundary.change.mockResolvedValue({ ok: true });
  const rendered = render(view(ready()));
  await clickAdd();
  boundary.session = {
    status: "authenticated",
    user: { email: "other@example.test" },
  };
  rendered.rerender(view(ready()));
  expect(
    screen
      .getByRole("button", { name: "Saved to cart", hidden: true })
      .closest("[data-cart-private]")
      ?.getAttribute("inert"),
  ).toBe("");
  rendered.rerender(view(ready("other@example.test", 0)));
  expect(screen.getByRole("button", { name: "Add to cart" })).toBeTruthy();
  expect(screen.queryByText("Saved.", { exact: false })).toBeNull();
});

it.each(["pointerup", "pointercancel", "blur", "pagehide"])(
  "keeps a started pointer activation alive until %s, then makes concealed controls inert",
  async (finish) => {
    vi.useFakeTimers();
    const rendered = render(view(ready()));
    const button = screen.getByRole("button", { name: "Add to cart" });
    const region = button.closest("[data-cart-private]")!;
    fireEvent.pointerDown(button, { button: 1 });
    fireEvent.pointerDown(button, { button: 0 });
    fireEvent(window, new Event("focus"));
    expect(region.getAttribute("aria-hidden")).toBe("true");
    expect(region.hasAttribute("inert")).toBe(false);
    fireEvent(window, new Event(finish));
    await act(async () => vi.advanceTimersByTime(0));
    expect(region.hasAttribute("inert")).toBe(true);
    rendered.unmount();
    expect(vi.getTimerCount()).toBe(0);
  },
);
