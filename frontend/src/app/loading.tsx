import { container, eyebrow } from "@/components/storefront-layout";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
export default function Loading() {
  return (
    <main id="main" className={cn(container, "py-16")}>
      <div role="status" aria-label="Loading collection">
        <p className={eyebrow}>A MOMENT OF SPACE</p>
        <h1 className="mb-8 font-serif text-4xl">Gathering the collection…</h1>
        <div className="grid gap-6 sm:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton
              className="h-[250px] [&:not(:first-child)]:hidden sm:[&:not(:first-child)]:block rounded-none bg-muted motion-reduce:animate-none"
              aria-hidden="true"
              key={i}
            />
          ))}
        </div>
      </div>
    </main>
  );
}
