// @vitest-environment jsdom
import { afterEach, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { ShareCollection } from "../src/components/share-collection";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function stubClipboard(writeText: (text: string) => Promise<void>) {
  vi.stubGlobal("navigator", { clipboard: { writeText } });
}

const share = () => screen.getByRole("button", { name: "Share results" });

it("copies the absolute canonical URL and announces success", async () => {
  const writeText = vi.fn().mockResolvedValue(undefined);
  stubClipboard(writeText);
  render(<ShareCollection href="/?q=oak&page=2#collection" />);
  await act(async () => fireEvent.click(share()));
  expect(writeText).toHaveBeenCalledWith(
    `${window.location.origin}/?q=oak&page=2#collection`,
  );
  expect(screen.getByText("Collection link copied.")).toBeTruthy();
  expect(screen.queryByRole("textbox", { name: "Collection link" })).toBeNull();
});

it("offers a selectable link when the clipboard is unavailable", async () => {
  stubClipboard(() => Promise.reject(new Error("denied")));
  render(<ShareCollection href="/?q=oak#collection" />);
  await act(async () => fireEvent.click(share()));
  const link = screen.getByRole<HTMLInputElement>("textbox", {
    name: "Collection link",
  });
  expect(link.value).toBe(`${window.location.origin}/?q=oak#collection`);
  expect(link.readOnly).toBe(true);
  expect(screen.queryByText("Collection link copied.")).toBeNull();
  expect(screen.getByText(/Couldn’t copy automatically/)).toBeTruthy();
  fireEvent.focus(link);
  expect(link.selectionStart).toBe(0);
  expect(link.selectionEnd).toBe(link.value.length);
});

it("does not claim a changed selection was copied when a write finishes late", async () => {
  let finish: () => void = () => undefined;
  stubClipboard(() => new Promise<void>((resolve) => (finish = resolve)));
  const { rerender } = render(
    <ShareCollection key="/?q=a#collection" href="/?q=a#collection" />,
  );
  fireEvent.click(share());
  expect((share() as HTMLButtonElement).disabled).toBe(true);
  rerender(<ShareCollection key="/?q=b#collection" href="/?q=b#collection" />);
  expect((share() as HTMLButtonElement).disabled).toBe(false);
  await act(async () => finish());
  expect(screen.queryByText("Collection link copied.")).toBeNull();
});

it("does not offer the old link when a failure finishes late", async () => {
  let fail: (error: Error) => void = () => undefined;
  stubClipboard(() => new Promise<void>((_resolve, reject) => (fail = reject)));
  const { rerender } = render(
    <ShareCollection key="a" href="/?q=a#collection" />,
  );
  fireEvent.click(share());
  rerender(<ShareCollection key="b" href="/?q=b#collection" />);
  await act(async () => fail(new Error("late")));
  expect(screen.queryByRole("textbox", { name: "Collection link" })).toBeNull();
});
