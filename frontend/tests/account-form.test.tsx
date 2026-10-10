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
import type { AccountIntent } from "../src/lib/account-return";

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

function withReplace(replace: ReturnType<typeof vi.fn>) {
  const location = window.location;
  Object.defineProperty(window, "location", {
    configurable: true,
    value: { replace },
  });
  return () => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: location,
    });
  };
}

it("returns to the selected product and carries that intent into registration", async () => {
  const intent: AccountIntent = {
    destination: "/products/7?category=lighting&q=lamp",
    query: "?product=7&category=lighting&q=lamp",
  };
  const replace = vi.fn();
  const restore = withReplace(replace);
  try {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ detail: "no" }), { status: 401 }),
        )
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ authenticated: true }), {
            status: 200,
          }),
        ),
    );
    const rendered = render(<AccountForm mode="login" intent={intent} />);
    expect(
      screen
        .getByRole("link", { name: "Create an account" })
        .getAttribute("href"),
    ).toBe("/register?product=7&category=lighting&q=lamp");
    fillAndSubmit();
    await screen.findByRole("alert");
    expect(replace).not.toHaveBeenCalled();
    fillAndSubmit();
    await waitFor(() =>
      expect(replace).toHaveBeenCalledExactlyOnceWith(
        "/products/7?category=lighting&q=lamp",
      ),
    );
    rendered.unmount();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ registered: true }), { status: 201 }),
      ),
    );
    render(<AccountForm mode="register" intent={intent} />);
    fillAndSubmit("register");
    await screen.findByText("Your account is ready. Sign in to continue.");
    expect(
      screen
        .getByRole("link", { name: "Continue to sign in" })
        .getAttribute("href"),
    ).toBe("/login?product=7&category=lighting&q=lamp");
  } finally {
    restore();
  }
});

it("ignores an open redirect supplied as the sign-in destination", async () => {
  const replace = vi.fn();
  const restore = withReplace(replace);
  try {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ authenticated: true }), {
            status: 200,
          }),
        ),
    );
    render(
      <AccountForm
        mode="login"
        intent={{
          destination: "https://attacker.example/products/1",
          query: "?next=https://attacker.example",
        }}
      />,
    );
    expect(
      screen
        .getByRole("link", { name: "Create an account" })
        .getAttribute("href"),
    ).toBe("/register");
    fillAndSubmit();
    await waitFor(() =>
      expect(replace).toHaveBeenCalledExactlyOnceWith("/#collection"),
    );
  } finally {
    restore();
  }
});

it.each(["login", "register"] as const)(
  "announces throttling in %s without replaying credentials",
  async (mode) => {
    const request = vi.fn().mockResolvedValue(
      new Response("not JSON", {
        status: 429,
        headers: { "Retry-After": "1" },
      }),
    );
    vi.stubGlobal("fetch", request);
    render(<AccountForm mode={mode} />);
    fillAndSubmit(mode);
    const feedback = await screen.findByRole("alert");
    expect(feedback.textContent).toBe(
      "Too many requests. Wait 1 second, then try again.",
    );
    await waitFor(() => expect(document.activeElement).toBe(feedback));
    expect(request).toHaveBeenCalledOnce();
    expect(
      (screen.getByLabelText("Password") as HTMLInputElement).disabled,
    ).toBe(false);
  },
);

it.each(["login", "register"] as const)(
  "toggles %s password visibility without changing credentials or submitting",
  async (mode) => {
    const request = vi
      .fn()
      .mockResolvedValue(new Response("{}", { status: 401 }));
    vi.stubGlobal("fetch", request);
    render(<AccountForm mode={mode} />);
    const password = screen.getByLabelText("Password") as HTMLInputElement;
    expect(password.type).toBe("password");
    expect(password.autocomplete).toBe(
      mode === "login" ? "current-password" : "new-password",
    );
    fireEvent.change(password, { target: { value: "  fictional-password  " } });
    const toggle = screen.getByRole("button", { name: "Show password" });
    expect(toggle.getAttribute("type")).toBe("button");
    expect(toggle.getAttribute("aria-pressed")).toBe("false");
    fireEvent.click(toggle);
    expect(password.type).toBe("text");
    expect(password.value).toBe("  fictional-password  ");
    expect(
      screen
        .getByRole("button", { name: "Hide password" })
        .getAttribute("aria-pressed"),
    ).toBe("true");
    fireEvent.click(screen.getByRole("button", { name: "Hide password" }));
    expect(password.type).toBe("password");
    expect(password.value).toBe("  fictional-password  ");
    expect(request).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("Email address"), {
      target: { value: "fiction@example.test" },
    });
    fireEvent.submit(
      screen.getByRole("form", {
        name: mode === "login" ? "Sign in" : "Create account",
      }),
    );
    await waitFor(() => expect(request).toHaveBeenCalledOnce());
    expect(JSON.parse(request.mock.calls[0][1].body).password).toBe(
      "  fictional-password  ",
    );
  },
);
