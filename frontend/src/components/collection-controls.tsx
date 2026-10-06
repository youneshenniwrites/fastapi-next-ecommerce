"use client";
import { useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import {
  collectionHref,
  hasActiveFilters,
  maxQueryLength,
  sortLabels,
  sorts,
  type CollectionFilters,
} from "@/lib/collection-url";

export function CollectionControls({
  filters,
}: {
  filters: CollectionFilters;
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [text, setText] = useState(filters.query);
  const [seen, setSeen] = useState(filters.query);
  // Back/Forward and Clear change the URL-owned query; adopt it without
  // remounting the input so keyboard focus is kept.
  if (seen !== filters.query) {
    setSeen(filters.query);
    setText(filters.query);
  }
  const current = collectionHref(filters);

  function go(next: CollectionFilters) {
    const href = collectionHref(next);
    startTransition(() => {
      if (href === current) router.refresh();
      else router.push(href, { scroll: false });
    });
  }

  return (
    <div className="border-y border-border py-4">
      <div className="flex flex-wrap items-center gap-4">
        <form
          role="search"
          action="/"
          method="get"
          aria-label="Search the collection"
          className="flex min-w-0 basis-full gap-2 md:flex-1 md:basis-auto"
          onSubmit={(event) => {
            event.preventDefault();
            go({ ...filters, query: text.trim(), page: 1 });
          }}
        >
          {filters.inStock && <input type="hidden" name="in_stock" value="1" />}
          {filters.sort !== "featured" && (
            <input type="hidden" name="sort" value={filters.sort} />
          )}
          <div className="relative min-w-0 flex-1">
            <Search
              className="pointer-events-none absolute left-3 top-3 size-4 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              className="h-10 pl-10"
              type="search"
              name="q"
              aria-label="Search collection"
              placeholder="Find something for your space…"
              value={text}
              maxLength={maxQueryLength}
              autoComplete="off"
              onChange={(event) => setText(event.target.value)}
            />
          </div>
          <Button
            type="submit"
            variant="outline"
            size="lg"
            className="min-h-10 shrink-0"
            disabled={pending}
          >
            {pending ? "Searching…" : "Search"}
          </Button>
        </form>
        <div className="flex min-h-11 w-28 shrink-0 items-center gap-2">
          <Checkbox
            id="in-stock"
            checked={filters.inStock}
            onCheckedChange={(checked) =>
              go({ ...filters, inStock: checked === true, page: 1 })
            }
            className="size-5"
          />
          <label
            htmlFor="in-stock"
            className="cursor-pointer whitespace-nowrap py-2 text-xs"
          >
            In stock only
          </label>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <label
            htmlFor="sort-products"
            className="w-10 shrink-0 whitespace-nowrap text-xs"
          >
            Sort by
          </label>
          <Select
            value={filters.sort}
            onValueChange={(value) => {
              const sort = sorts.find((candidate) => candidate === value);
              if (sort) go({ ...filters, sort, page: 1 });
            }}
          >
            <SelectTrigger
              id="sort-products"
              aria-label="Sort products"
              className="h-10 w-[180px]"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {sorts.map((sort) => (
                <SelectItem key={sort} value={sort}>
                  {sortLabels[sort]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      {hasActiveFilters(filters) && (
        <div className="mt-3">
          <Link
            href="/#collection"
            scroll={false}
            className="inline-flex min-h-11 items-center text-xs underline underline-offset-4 hover:no-underline"
          >
            Clear all filters
          </Link>
        </div>
      )}
    </div>
  );
}
