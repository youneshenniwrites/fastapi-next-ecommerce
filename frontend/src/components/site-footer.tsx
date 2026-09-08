import { ArrowUpRight } from "lucide-react";
import { Wordmark } from "@/components/site-header";
import { container } from "@/components/storefront-layout";
import { cn } from "@/lib/utils";
export function SiteFooter() {
  return (
    <footer
      className={cn(
        container,
        "flex flex-col gap-6 py-12 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between",
      )}
    >
      <div className="text-foreground">
        <Wordmark />
        <p className="mt-3 text-muted-foreground">
          Make space for what matters.
        </p>
      </div>
      <p>
        Fictional shop · Portfolio demonstration
        <br />
        Browse in GBP. Purchasing is not available yet.
      </p>
      <a
        className="inline-flex items-center gap-2 underline underline-offset-4"
        href="https://github.com/youneshenniwrites/fastapi-next-ecommerce"
      >
        Explore the project{" "}
        <ArrowUpRight className="size-4" aria-hidden="true" />
      </a>
    </footer>
  );
}
