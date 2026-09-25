// @vitest-environment jsdom
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
vi.mock("@/components/site-header", () => ({
  Wordmark: () => <span>VINDOR</span>,
}));
import { SiteFooter } from "@/components/site-footer";

afterEach(cleanup);

it("discloses sandbox restrictions in the shared footer without a stale purchase warning", () => {
  render(<SiteFooter />);
  const footer = within(screen.getByRole("contentinfo"));
  expect(footer.getByText(/sandbox payments only/i)).toBeTruthy();
  expect(footer.getByText(/no real charges or shipping/i)).toBeTruthy();
  expect(footer.queryByText(/purchasing is not available/i)).toBeNull();
});
