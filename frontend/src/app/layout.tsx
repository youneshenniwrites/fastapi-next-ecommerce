import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
export const metadata: Metadata = {
  title: { default: "FORME — Room to think", template: "%s | FORME" },
  description:
    "Considered objects for a calmer workspace. A fictional ecommerce portfolio.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <a href="#main" className="skip">
          Skip to content
        </a>
        <div
          className="announcement"
          role="region"
          aria-label="Collection note"
        >
          A little less clutter. A little more clarity.{" "}
          <span>THE WORKSPACE COLLECTION</span>
        </div>
        <header className="header">
          <Link className="wordmark" href="/" aria-label="FORME home">
            forme<span>®</span>
          </Link>
          <nav aria-label="Main navigation">
            <Link href="/#collection">The collection</Link>
            <Link href="/#approach">Our approach</Link>
          </nav>
          <span className="edition">OBJECTS FOR EVERYDAY FOCUS</span>
        </header>
        {children}
        <footer>
          <div>
            <Link className="wordmark" href="/">
              forme<span>®</span>
            </Link>
            <p>Make space for what matters.</p>
          </div>
          <p>
            Fictional shop · Portfolio demonstration
            <br />
            Browse in GBP. Purchasing is not available yet.
          </p>
          <a href="https://github.com/youneshenniwrites/fastapi-next-ecommerce">
            Explore the project ↗
          </a>
        </footer>
      </body>
    </html>
  );
}
