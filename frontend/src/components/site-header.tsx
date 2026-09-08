import Link from "next/link";
import { MobileNavigation } from "@/components/mobile-navigation";
import { container } from "@/components/storefront-layout";
import { cn } from "@/lib/utils";
export function Wordmark() {
  return (
    <Link
      href="/"
      aria-label="VINDOR home"
      className="inline-flex items-start font-serif text-[40px] font-bold leading-none tracking-[-2px]"
    >
      vindor
    </Link>
  );
}
export function SiteHeader() {
  return (
    <>
      <div
        className="bg-primary px-5 py-2.5 text-center text-[10px] text-primary-foreground"
        role="region"
        aria-label="Collection note"
      >
        A little less clutter. A little more clarity.
        <span className="ml-7 hidden text-[9px] tracking-widest sm:inline">
          THE WORKSPACE COLLECTION
        </span>
      </div>
      <header
        className={cn(
          container,
          "flex h-20 items-center justify-between border-b border-border sm:h-24",
        )}
      >
        <Wordmark />
        <nav
          aria-label="Main navigation"
          className="hidden gap-9 text-sm sm:flex"
        >
          <Link
            className="hover:underline underline-offset-8"
            href="/#collection"
          >
            The collection
          </Link>
          <Link
            className="hover:underline underline-offset-8"
            href="/#approach"
          >
            Our approach
          </Link>
        </nav>
        <span className="hidden text-[9px] tracking-widest text-muted-foreground lg:inline">
          OBJECTS FOR EVERYDAY FOCUS
        </span>
        <MobileNavigation />
      </header>
    </>
  );
}
