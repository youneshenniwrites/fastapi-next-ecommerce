import type { Metadata } from "next";
import { Suspense } from "react";
import { SiteHeader } from "@/components/site-header";
import { SiteFooter } from "@/components/site-footer";
import "./globals.css";
import { SessionProvider } from "@/components/session-provider";
import { CartRefreshWarning } from "@/components/cart-refresh-warning";
import {
  CartRoot,
  CartSnapshotUpdate,
  CartProvider,
} from "@/components/cart-provider";
import { readCartSnapshot } from "@/lib/cart-data";
export const metadata: Metadata = {
  title: { default: "VINDOR — Room to think", template: "%s | VINDOR" },
  description:
    "Considered objects for a calmer workspace. A fictional ecommerce portfolio.",
};
async function CartShell() {
  const snapshot = await readCartSnapshot();
  return (
    <>
      <CartSnapshotUpdate snapshot={snapshot} />
      <CartProvider snapshot={snapshot}>
        <SiteHeader />
      </CartProvider>
    </>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <a
          href="#main"
          className="sr-only z-[60] bg-background p-3 focus:not-sr-only focus:absolute focus:left-5 focus:top-3"
        >
          Skip to content
        </a>
        <SessionProvider>
          <CartRoot>
            <Suspense fallback={<SiteHeader />}>
              <CartShell />
            </Suspense>
            <CartRefreshWarning />
            {children}
          </CartRoot>
        </SessionProvider>
        <SiteFooter />
      </body>
    </html>
  );
}
