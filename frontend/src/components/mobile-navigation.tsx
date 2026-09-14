"use client";
import Link from "next/link";
import { AccountLink } from "@/components/account-link";
import { CartLink } from "@/components/cart-link";
import { useEffect, useSyncExternalStore } from "react";
import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetClose,
} from "@/components/ui/sheet";

// The sheet trigger lives in the streaming server-rendered header: focus and
// session revalidation can remount it while a tap is in flight, which would
// discard a useState open flag and swallow the tap. Keep the open flag in a
// module store so every header instance observes the same menu intent.
let navigationOpen = false;
const navigationListeners = new Set<() => void>();
function subscribeNavigation(notify: () => void) {
  navigationListeners.add(notify);
  return () => {
    navigationListeners.delete(notify);
  };
}
function setNavigationOpen(next: boolean) {
  if (navigationOpen === next) return;
  navigationOpen = next;
  navigationListeners.forEach((notify) => notify());
}
function useNavigationOpen() {
  return useSyncExternalStore(
    subscribeNavigation,
    () => navigationOpen,
    () => false,
  );
}
export function MobileNavigation() {
  const open = useNavigationOpen();
  useEffect(() => {
    // Match Tailwind's sm breakpoint; the sheet is portaled outside its wrapper.
    const desktop = window.matchMedia("(min-width: 40rem)");
    const closeOnDesktop = (event: MediaQueryListEvent) => {
      if (event.matches) setNavigationOpen(false);
    };
    desktop.addEventListener("change", closeOnDesktop);
    return () => desktop.removeEventListener("change", closeOnDesktop);
  }, []);
  return (
    <div className="sm:hidden">
      <Sheet open={open} onOpenChange={setNavigationOpen}>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="size-11"
            aria-label="Open navigation"
          >
            <Menu aria-hidden="true" />
          </Button>
        </SheetTrigger>
        <SheetContent className="w-[min(85vw,360px)]">
          <SheetHeader className="px-6 pt-16">
            <SheetTitle className="font-serif text-3xl">
              Explore VINDOR
            </SheetTitle>
            <SheetDescription>
              Considered objects for a calmer workspace.
            </SheetDescription>
          </SheetHeader>
          <nav aria-label="Mobile navigation" className="flex flex-col px-6">
            <SheetClose asChild>
              <Link
                className="border-b border-border py-5 text-base"
                href="/#collection"
              >
                The collection
              </Link>
            </SheetClose>
            <SheetClose asChild>
              <Link
                className="border-b border-border py-5 text-base"
                href="/#approach"
              >
                Our approach
              </Link>
            </SheetClose>
            <AccountLink
              className="border-b border-border py-5 text-base"
              onClick={() => setNavigationOpen(false)}
            />
            <CartLink
              className="border-b border-border py-5 text-base"
              onClick={() => setNavigationOpen(false)}
            />
          </nav>
          <p className="mt-auto p-6 text-xs text-muted-foreground">
            Fictional shop · Browse in GBP
          </p>
        </SheetContent>
      </Sheet>
    </div>
  );
}
