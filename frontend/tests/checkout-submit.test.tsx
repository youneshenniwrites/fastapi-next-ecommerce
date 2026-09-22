// @vitest-environment jsdom
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { CheckoutResult } from "../src/app/orders/actions";

const mocks = vi.hoisted(() => ({ session: vi.fn(), navigate: vi.fn() }));
vi.mock("@/components/session-provider", () => ({ useSession: mocks.session }));
import { CheckoutSubmit } from "../src/components/checkout-submit";

const owner = "a@example.com";
const authenticated = (email = owner) => ({
  status: "authenticated",
  user: { email },
});

beforeEach(() => {
  mocks.session.mockReturnValue(authenticated());
  // Preserve the real DOM window for React while observing navigation without
  // relying on jsdom's unimplemented cross-document navigation.
  const realWindow = window;
  vi.stubGlobal(
    "window",
    new Proxy(realWindow, {
      get(target, property) {
        return property === "location"
          ? { assign: mocks.navigate }
          : Reflect.get(target, property, target);
      },
    }),
  );
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

function pendingCheckout() {
  let resolve!: (result: CheckoutResult) => void;
  const response = new Promise<CheckoutResult>((done) => {
    resolve = done;
  });
  const action = vi.fn(() => response);
  const view = (currentOwner = owner) => (
    <CheckoutSubmit action={action} label="Place order" owner={currentOwner} />
  );
  const rendered = render(view());
  fireEvent.submit(screen.getByRole("button").closest("form")!);
  expect(action).toHaveBeenCalledTimes(1);
  return {
    ...rendered,
    view,
    complete: async () => {
      await act(async () => {
        resolve({ error: "", location: "/orders/7" });
        await response;
      });
    },
  };
}

it("does not navigate when an action completes after checkout unmounts", async () => {
  const checkout = pendingCheckout();
  checkout.unmount();
  await checkout.complete();
  expect(mocks.navigate).not.toHaveBeenCalled();
});

for (const session of [{ status: "guest" }, authenticated("b@example.com")])
  it(`does not navigate after the session becomes ${session.status}`, async () => {
    const checkout = pendingCheckout();
    mocks.session.mockReturnValue(session);
    checkout.rerender(checkout.view());
    await checkout.complete();
    expect(mocks.navigate).not.toHaveBeenCalled();
  });

it("does not apply a previous owner's result to a new owner", async () => {
  const checkout = pendingCheckout();
  mocks.session.mockReturnValue(authenticated("b@example.com"));
  checkout.rerender(checkout.view("b@example.com"));
  await checkout.complete();
  expect(mocks.navigate).not.toHaveBeenCalled();
});

it("retains pending state and waits for the same account to authenticate before navigation", async () => {
  const checkout = pendingCheckout();
  const button = screen.getByRole("button") as HTMLButtonElement;
  expect(button.disabled).toBe(true);
  mocks.session.mockReturnValue({ status: "loading" });
  checkout.rerender(checkout.view());
  expect(screen.getByRole("button")).toBe(button);
  expect(button.disabled).toBe(true);
  await checkout.complete();
  expect(mocks.navigate).not.toHaveBeenCalled();
  mocks.session.mockReturnValue(authenticated());
  checkout.rerender(checkout.view());
  expect(mocks.navigate).toHaveBeenCalledExactlyOnceWith("/orders/7");
});
