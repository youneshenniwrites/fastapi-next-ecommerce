import { Skeleton } from "@/components/ui/skeleton";

export function CatalogSkeleton() {
  return (
    <div role="status" aria-label="Loading collection" aria-busy="true">
      <span className="sr-only">Loading collection…</span>
      <div aria-hidden="true">
        <div className="flex flex-wrap items-center gap-4 border-y border-border py-4">
          <Skeleton className="h-10 min-w-0 basis-full md:flex-1 md:basis-auto" />
          <Skeleton className="h-11 w-24 shrink-0" />
          <div className="ml-auto flex items-center gap-2">
            <Skeleton className="h-4 w-10" />
            <Skeleton className="h-10 w-[180px]" />
          </div>
        </div>
        <Skeleton className="my-5 h-4 w-16" />
        <div className="grid grid-cols-2 gap-x-4 gap-y-8 lg:grid-cols-3 lg:gap-x-6 lg:gap-y-10">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div key={i}>
              <Skeleton className="aspect-[6/5] w-full rounded-none" />
              <div className="mt-4 flex flex-col gap-1 lg:flex-row lg:justify-between lg:gap-3">
                <Skeleton className="h-5 w-3/5" />
                <Skeleton className="h-4 w-12" />
              </div>
              <Skeleton className="mt-2 h-4 w-4/5" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
