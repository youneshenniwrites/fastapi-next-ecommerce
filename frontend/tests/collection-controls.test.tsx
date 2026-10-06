// @vitest-environment jsdom
import { afterEach, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { CollectionControls } from "../src/components/collection-controls";
import { defaultFilters } from "../src/lib/collection-url";

const router = vi.hoisted(() => ({ push: vi.fn(), refresh: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => router }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const box = () => screen.getByRole<HTMLInputElement>("searchbox");

it("changes the URL only when the search is submitted", async () => {
  render(<CollectionControls filters={{ ...defaultFilters, page: 3 }} />);
  fireEvent.change(box(), { target: { value: "  Oak  " } });
  expect(router.push).not.toHaveBeenCalled();
  await act(async () => {
    fireEvent.submit(screen.getByRole("search"));
  });
  expect(router.push).toHaveBeenCalledWith("/?q=Oak#collection", {
    scroll: false,
  });
});

it("keeps other filters, resets the page and refreshes an unchanged selection", async () => {
  render(
    <CollectionControls
      filters={{ query: "Oak", inStock: true, sort: "name", page: 2 }}
    />,
  );
  await act(async () => {
    fireEvent.submit(screen.getByRole("search"));
  });
  expect(router.push).toHaveBeenCalledWith(
    "/?q=Oak&in_stock=1&sort=name#collection",
    { scroll: false },
  );
  cleanup();
  render(<CollectionControls filters={{ ...defaultFilters, query: "Oak" }} />);
  await act(async () => {
    fireEvent.submit(screen.getByRole("search"));
  });
  expect(router.refresh).toHaveBeenCalledTimes(1);
});

it("toggles stock from the current selection and resets to page one", async () => {
  render(<CollectionControls filters={{ ...defaultFilters, page: 3 }} />);
  await act(async () => {
    fireEvent.click(screen.getByRole("checkbox", { name: "In stock only" }));
  });
  expect(router.push).toHaveBeenCalledWith("/?in_stock=1#collection", {
    scroll: false,
  });
});

it("adopts a changed URL query and offers a way to clear filters", () => {
  const { rerender } = render(
    <CollectionControls filters={{ ...defaultFilters, query: "Oak" }} />,
  );
  expect(box().value).toBe("Oak");
  expect(
    screen
      .getByRole("link", { name: "Clear all filters" })
      .getAttribute("href"),
  ).toBe("/#collection");
  rerender(<CollectionControls filters={defaultFilters} />);
  expect(box().value).toBe("");
  expect(screen.queryByRole("link", { name: "Clear all filters" })).toBeNull();
});

it("limits search text to the API maximum", () => {
  render(<CollectionControls filters={defaultFilters} />);
  expect(box().maxLength).toBe(100);
});
