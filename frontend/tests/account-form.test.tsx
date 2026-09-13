// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { renderToString } from "react-dom/server";
import { AccountForm } from "../src/components/account-form";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function fillAndSubmit(mode: "login" | "register" = "login") {
  fireEvent.change(screen.getByLabelText("Email address"), {
    target: { value: "person@example.test" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "password123" },
  });
  fireEvent.submit(
    screen.getByRole("form", {
      name: mode === "login" ? "Sign in" : "Create account",
    }),
  );
}

describe("account form feedback", () => {
  it("keeps credential inputs disabled in server HTML until submit handling attaches", () => {
    const document = new DOMParser().parseFromString(
      renderToString(<AccountForm mode="login" />),
      "text/html",
    );
    for (const name of ["email", "password"]) {
      expect(
        (document.querySelector(`[name="${name}"]`) as HTMLInputElement)
          .disabled,
      ).toBe(true);
    }
    expect(document.querySelector("form")?.getAttribute("aria-busy")).toBe(
      "true",
    );
  });
  it("rejects invalid input before sending credentials", async () => {
    const request = vi.fn();
    vi.stubGlobal("fetch", request);
    render(<AccountForm mode="login" />);
    fireEvent.submit(screen.getByRole("form", { name: "Sign in" }));
    await screen.findByText("Enter your email address.");
    expect(request).not.toHaveBeenCalled();
  });

  it.each([
    ["login", 401, "Email or password is incorrect. Please try again."],
    ["login", 422, "Check your email and password and try again."],
    ["login", 503, "Sign-in is temporarily unavailable. Please try again."],
    [
      "register",
      400,
      "Unable to create this account. Try signing in or use another email.",
    ],
    [
      "register",
      503,
      "We couldn't confirm registration. Try signing in before registering again.",
    ],
  ] as const)(
    "shows safe %s feedback for status %s",
    async (mode, status, message) => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue(
          new Response(JSON.stringify({ detail: "private internal error" }), {
            status,
          }),
        ),
      );
      render(<AccountForm mode={mode} />);
      fillAndSubmit(mode);
      const feedback = await screen.findByText(message);
      await waitFor(() => expect(document.activeElement).toBe(feedback));
      expect(screen.queryByText("private internal error")).toBeNull();
      expect(
        (screen.getByLabelText("Password") as HTMLInputElement).disabled,
      ).toBe(false);
    },
  );

  it("prevents duplicate submissions while pending, then confirms registration", async () => {
    let finish!: (value: Response) => void;
    const request = vi.fn().mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          finish = resolve;
        }),
    );
    vi.stubGlobal("fetch", request);
    render(<AccountForm mode="register" />);
    fillAndSubmit("register");
    await waitFor(() => expect(request).toHaveBeenCalledTimes(1));
    expect(
      (screen.getByLabelText("Password") as HTMLInputElement).disabled,
    ).toBe(true);
    await act(async () => {
      fireEvent.submit(screen.getByRole("form", { name: "Create account" }));
    });
    expect(request).toHaveBeenCalledTimes(1);
    expect(request.mock.calls[0][0]).toBe("/api/session/register");
    expect(request.mock.calls[0][1]).toMatchObject({
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: "person@example.test",
        password: "password123",
      }),
    });
    finish(new Response(JSON.stringify({ registered: true })));
    const success = await screen.findByText(
      "Your account is ready. Sign in to continue.",
    );
    expect(success.textContent).toBe(
      "Your account is ready. Sign in to continue.",
    );
    expect(screen.queryByLabelText("Password")).toBeNull();
    expect(request).toHaveBeenCalledTimes(1);
  });

  it.each(["login", "register"] as const)(
    "explains a %s transport failure and allows another attempt",
    async (mode) => {
      const request = vi
        .fn()
        .mockRejectedValue(new TypeError("network failed"));
      vi.stubGlobal("fetch", request);
      render(<AccountForm mode={mode} />);
      fillAndSubmit(mode);
      await screen.findByText(
        mode === "login"
          ? "We couldn't connect. Check your connection and try again."
          : "We couldn't confirm registration. Check your connection and try signing in.",
      );
      fillAndSubmit(mode);
      await waitFor(() => expect(request).toHaveBeenCalledTimes(2));
    },
  );
});
