import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import type { components } from "@/lib/api/schema";
import { collectionHref, type CollectionFilters } from "@/lib/collection-url";
import { cn } from "@/lib/utils";

export type CategoryCount = components["schemas"]["CategoryCount"];

function label(name: string, count: number) {
  const noun = count === 1 ? "object" : "objects";
  return `${name}, ${count} ${noun}`;
}

export function CategoryNav({
  categories,
  filters,
}: {
  categories: CategoryCount[];
  filters: CollectionFilters;
}) {
  const allCount = categories.reduce(
    (sum, category) => sum + category.count,
    0,
  );
  const items = [
    { slug: "", name: "All", count: allCount },
    ...categories.map((category) => ({
      slug: category.slug,
      name: category.name,
      count: category.count,
    })),
  ];
  return (
    <nav aria-label="Categories" className="mb-4 p-1">
      <ul className="flex flex-wrap gap-2">
        {items.map((item) => {
          const current = item.slug === filters.category;
          return (
            <li key={item.slug || "all"}>
              <Link
                href={collectionHref({
                  ...filters,
                  category: item.slug,
                  page: 1,
                })}
                aria-current={current ? "page" : undefined}
                aria-label={label(item.name, item.count)}
                className={cn(
                  buttonVariants({
                    variant: current ? "default" : "outline",
                    size: "lg",
                  }),
                  "min-h-11 whitespace-normal text-left",
                )}
              >
                {item.name}
                <span aria-hidden="true">{item.count}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
