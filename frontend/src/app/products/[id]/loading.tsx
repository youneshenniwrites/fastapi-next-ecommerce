import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { container } from "@/components/storefront-layout";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export default function ProductLoading() {
  return (
    <main id="main" className={cn(container, "py-10 pb-20")}>
      <Link
        className="mb-8 inline-flex items-center gap-2 text-sm hover:underline"
        href="/#collection"
      >
        <ArrowLeft className="size-4" aria-hidden="true" /> Back to the
        collection
      </Link>
      <div role="status" aria-label="Loading product" aria-busy="true">
        <span className="sr-only">Loading product…</span>
        <div
          aria-hidden="true"
          className="grid items-start gap-8 md:grid-cols-2 lg:gap-16"
        >
          <Skeleton className="aspect-[6/5] w-full rounded-none" />
          <div className="min-w-0 py-4">
            <Skeleton className="mb-5 h-3 w-40" />
            <Skeleton className="mb-6 h-12 w-4/5" />
            <Skeleton className="mb-6 h-8 w-24" />
            <Skeleton className="h-7 w-full" />
            <Skeleton className="mt-6 h-7 w-24" />
            <Skeleton className="mt-8 h-32 w-full" />
          </div>
        </div>
      </div>
    </main>
  );
}
