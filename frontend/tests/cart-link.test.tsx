// @vitest-environment jsdom
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { CartLink } from "../src/components/cart-link";

vi.mock("@/components/cart-provider", () => ({
  useCart: () => ({ count: 0, concealed: false, state: { status: "ready" } }),
}));

const assign = vi.fn();

afterEach(() => {
  cleanup();
  assign.mockClear();
});

function installLocation() {
  const location = window.location;
  vi.stubGlobal("location", { ...location, assign });
}

function link() {
  return screen.getByRole("link", { name: "Cart" });
}

function pointer(
  type: string,
  init: PointerEventInit & { pointerType?: string },
) {
  const event = new PointerEvent(type, {
    bubbles: true,
    cancelable: true,
    ...init,
  });
  Object.defineProperty(event, "pointerType", { value: init.pointerType });
  return event;
}

it("opens the cart on a mouse press and ignores a modified press", () => {
  installLocation();
  render(<CartLink />);
  fireEvent(
    link(),
    pointer("pointerdown", { button: 0, pointerType: "mouse" }),
  );
  expect(assign).toHaveBeenCalledWith("/cart");
  assign.mockClear();
  fireEvent(
    link(),
    pointer("pointerdown", { button: 0, pointerType: "mouse", metaKey: true }),
  );
  expect(assign).not.toHaveBeenCalled();
});

it("does not open the cart when a touch starts or scrolls", () => {
  installLocation();
  const { unmount } = render(<CartLink />);
  link().dispatchEvent(
    pointer("pointerdown", {
      button: 0,
      pointerId: 1,
      pointerType: "touch",
      clientX: 4,
      clientY: 4,
    }),
  );
  expect(assign).not.toHaveBeenCalled();
  unmount();
  window.dispatchEvent(
    pointer("pointerup", {
      pointerId: 1,
      pointerType: "touch",
      clientX: 40,
      clientY: 4,
    }),
  );
  expect(assign).not.toHaveBeenCalled();
});

it("opens the cart when a touch ends after the header link is gone", () => {
  installLocation();
  const { unmount } = render(<CartLink />);
  link().dispatchEvent(
    pointer("pointerdown", {
      button: 0,
      pointerId: 2,
      pointerType: "touch",
      clientX: 4,
      clientY: 4,
    }),
  );
  unmount();
  window.dispatchEvent(
    pointer("pointerup", {
      pointerId: 2,
      pointerType: "touch",
      clientX: 6,
      clientY: 5,
    }),
  );
  expect(assign).toHaveBeenCalledWith("/cart");
});

it("leaves a completed touch on the live link to the browser", () => {
  installLocation();
  render(<CartLink />);
  link().dispatchEvent(
    pointer("pointerdown", {
      button: 0,
      pointerId: 3,
      pointerType: "touch",
      clientX: 4,
      clientY: 4,
    }),
  );
  window.dispatchEvent(
    pointer("pointerup", {
      pointerId: 3,
      pointerType: "touch",
      clientX: 5,
      clientY: 4,
    }),
  );
  expect(assign).not.toHaveBeenCalled();
});
