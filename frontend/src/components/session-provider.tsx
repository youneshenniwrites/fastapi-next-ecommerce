"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { components } from "@/lib/api/schema";

type User = Pick<components["schemas"]["UserRead"], "email" | "created_at">;
type Session =
  | { status: "loading" }
  | { status: "guest" }
  | { status: "error" }
  | { status: "authenticated"; user: User };
const SessionContext = createContext<Session>({ status: "loading" });
export function useSession() {
  return useContext(SessionContext);
}

// Only the public shell is rendered on the server. Private data is fetched with
// cookies through the same-origin handler; never serialize a token into React.
export function SessionProvider({ children }: { children: ReactNode }) {
  const [snapshot, setSnapshot] = useState<Session>();
  useEffect(() => {
    let controller: AbortController | undefined;
    let active = true;
    async function refresh() {
      controller?.abort();
      if (document.visibilityState !== "visible") {
        setSnapshot(undefined);
        return;
      }
      const current = new AbortController();
      controller = current;
      setSnapshot({ status: "loading" });
      try {
        const response = await fetch("/api/session/me", {
          cache: "no-store",
          signal: AbortSignal.any([current.signal, AbortSignal.timeout(10000)]),
        });
        let session: Session;
        if (response.status === 401) session = { status: "guest" };
        else if (!response.ok) session = { status: "error" };
        else {
          const user: components["schemas"]["UserRead"] = await response.json();
          session = {
            status: "authenticated",
            user: { email: user.email, created_at: user.created_at },
          };
        }
        if (
          active &&
          !current.signal.aborted &&
          document.visibilityState === "visible"
        )
          setSnapshot(session);
      } catch {
        if (active && !current.signal.aborted) setSnapshot({ status: "error" });
      }
    }
    function hide() {
      controller?.abort();
      setSnapshot(undefined);
    }
    function visibility() {
      if (document.visibilityState === "visible") void refresh();
      else hide();
    }
    void refresh();
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void refresh();
    }, 60000);
    window.addEventListener("pageshow", refresh);
    window.addEventListener("pagehide", hide);
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", visibility);
    return () => {
      window.clearInterval(timer);
      active = false;
      controller?.abort();
      window.removeEventListener("pageshow", refresh);
      window.removeEventListener("pagehide", hide);
      window.removeEventListener("focus", refresh);
      document.removeEventListener("visibilitychange", visibility);
    };
  }, []);
  const session = snapshot ?? { status: "loading" as const };
  return (
    <SessionContext.Provider value={session}>
      {children}
    </SessionContext.Provider>
  );
}
