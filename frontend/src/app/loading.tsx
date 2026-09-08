import { Skeleton } from "@/components/ui/skeleton";
export default function Loading() {
  return (
    <main id="main" className="loading">
      <div role="status" aria-label="Loading collection">
        <p className="eyebrow">A MOMENT OF SPACE</p>
        <h1>Gathering the collection…</h1>
        <div className="skeleton-grid">
          {[1, 2, 3].map((i) => (
            <Skeleton
              className="skeleton h-[250px] rounded-none bg-muted motion-reduce:animate-none"
              aria-hidden="true"
              key={i}
            />
          ))}
        </div>
      </div>
    </main>
  );
}
