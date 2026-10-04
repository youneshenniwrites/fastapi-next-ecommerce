// @vitest-environment jsdom
import { act } from "@testing-library/react";
import { renderToString } from "react-dom/server";
import { hydrateRoot, type Root } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { AccountLink } from "../src/components/account-link";
import { useSession } from "../src/components/session-provider";

vi.mock("../src/components/session-provider", () => ({ useSession: vi.fn() }));

const session = vi.mocked(useSession);
let root: Root | undefined;
afterEach(async () => {
  await act(async () => root?.unmount());
  root = undefined;
  document.body.innerHTML = "";
  vi.clearAllMocks();
});

it.each([
  [{ status: "guest" }, "Sign in", "/login"],
  [
    {
      status: "authenticated",
      user: { email: "customer@example.test", created_at: "2026-10-04" },
    },
    "My account",
    "/account",
  ],
  [{ status: "error" }, "My account", "/account"],
] as const)(
  "hydrates the streamed placeholder when the session has already become %j",
  async (resolved, label, href) => {
    session.mockReturnValue({ status: "loading" });
    document.body.innerHTML = renderToString(<AccountLink />);
    const placeholder = document.querySelector('[aria-busy="true"]');
    expect(placeholder?.textContent).toBe("Account");

    // The surrounding provider can resolve before this streamed boundary hydrates.
    session.mockReturnValue(resolved);
    const recoverableError = vi.fn();
    await act(async () => {
      root = hydrateRoot(document.body, <AccountLink />, {
        onRecoverableError: recoverableError,
      });
    });
    expect(recoverableError).not.toHaveBeenCalled();
    expect(document.querySelector("a")?.textContent).toBe(label);
    expect(document.querySelector("a")?.getAttribute("href")).toBe(href);

    // A later session recheck must still hide the old account action.
    session.mockReturnValue({ status: "loading" });
    await act(async () => root!.render(<AccountLink />));
    expect(document.querySelector("a")).toBeNull();
    expect(document.querySelector('[aria-busy="true"]')?.textContent).toBe(
      "Account",
    );
    session.mockReturnValue({ status: "guest" });
    await act(async () => root!.render(<AccountLink />));
    expect(document.querySelector("a")?.textContent).toBe("Sign in");
  },
);
