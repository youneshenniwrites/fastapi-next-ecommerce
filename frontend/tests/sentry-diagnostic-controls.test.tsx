// @vitest-environment jsdom
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
const mocks = vi.hoisted(() => ({
  authorize: vi.fn(),
  server: vi.fn(),
  capture: vi.fn(),
  flush: vi.fn(),
}));
vi.mock("@/app/diagnostics/sentry/actions", () => ({
  authorizeClientDiagnostic: mocks.authorize,
  captureServerDiagnostic: mocks.server,
}));
vi.mock("@sentry/nextjs", () => ({
  captureException: mocks.capture,
  flush: mocks.flush,
}));
import { SentryDiagnosticControls } from "../src/components/sentry-diagnostic-controls";
beforeEach(() => {
  vi.resetAllMocks();
  mocks.authorize.mockResolvedValue(true);
  mocks.server.mockResolvedValue({ flushed: true });
  mocks.flush.mockResolvedValue(true);
});
afterEach(cleanup);
it("sends the fixed browser event only after fresh authorization", async () => {
  render(<SentryDiagnosticControls />);
  fireEvent.click(screen.getByText("Test browser error"));
  expect(mocks.capture).not.toHaveBeenCalled();
  await waitFor(() =>
    expect(mocks.capture).toHaveBeenCalledWith(
      expect.objectContaining({
        message: "Development browser observability verification",
      }),
    ),
  );
  expect(mocks.authorize).toHaveBeenCalledOnce();
  expect(mocks.flush).toHaveBeenCalledWith(2000);
  expect(screen.getByRole("status").textContent).toContain("Confirm receipt");
});
it("does not capture when the server denies access", async () => {
  mocks.authorize.mockRejectedValue(new Error("404"));
  render(<SentryDiagnosticControls />);
  fireEvent.click(screen.getByText("Test browser error"));
  await waitFor(() =>
    expect(screen.getByRole("status").textContent).toContain("unavailable"),
  );
  expect(mocks.capture).not.toHaveBeenCalled();
});
it("uses the server action without duplicating a browser event", async () => {
  render(<SentryDiagnosticControls />);
  fireEvent.click(screen.getByText("Test server error"));
  await waitFor(() =>
    expect(screen.getByRole("status").textContent).toContain("Confirm receipt"),
  );
  expect(mocks.server).toHaveBeenCalledOnce();
  expect(mocks.capture).not.toHaveBeenCalled();
});
it("reports a transport timeout without claiming receipt", async () => {
  mocks.flush.mockResolvedValue(false);
  render(<SentryDiagnosticControls />);
  fireEvent.click(screen.getByText("Test browser error"));
  await waitFor(() =>
    expect(screen.getByRole("status").textContent).toContain("timed out"),
  );
});
