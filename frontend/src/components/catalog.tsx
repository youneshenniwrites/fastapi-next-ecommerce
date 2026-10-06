import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { ProductCard } from "@/components/product-card";
import { stateLayout } from "@/components/storefront-layout";
import { PageLink, ResultsStatus } from "@/components/collection-navigation";
import { ShareCollection } from "@/components/share-collection";
import type { Product } from "@/lib/catalog";
import {
  collectionHref,
  collectionQuery,
  hasActiveFilters,
  pageSize,
  pageWindow,
  totalPages,
  type CollectionFilters,
} from "@/lib/collection-url";

export type CatalogPage = {
  items: Product[];
  total: number;
  limit: number;
  skip: number;
};

const disabledStep =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-md border border-border px-3 text-xs opacity-50";

function Pagination({
  filters,
  pages,
}: {
  filters: CollectionFilters;
  pages: number;
}) {
  const at = (page: number) => collectionHref({ ...filters, page });
  return (
    <nav aria-label="Collection pages" className="mt-12">
      <ul className="flex flex-wrap items-center justify-center gap-2">
        <li>
          {filters.page > 1 ? (
            <PageLink href={at(filters.page - 1)} rel="prev">
              <ChevronLeft aria-hidden="true" /> Previous
            </PageLink>
          ) : (
            <span aria-disabled="true" className={disabledStep}>
              <ChevronLeft aria-hidden="true" /> Previous
            </span>
          )}
        </li>
        {pageWindow(filters.page, pages).map((page, index) =>
          page === null ? (
            <li
              key={`gap-${index}`}
              aria-hidden="true"
              className="px-1 text-muted-foreground"
            >
              …
            </li>
          ) : (
            <li key={page}>
              <PageLink
                href={at(page)}
                current={page === filters.page}
                aria-label={`Page ${page}`}
              >
                {page}
              </PageLink>
            </li>
          ),
        )}
        <li>
          {filters.page < pages ? (
            <PageLink href={at(filters.page + 1)} rel="next">
              Next <ChevronRight aria-hidden="true" />
            </PageLink>
          ) : (
            <span aria-disabled="true" className={disabledStep}>
              Next <ChevronRight aria-hidden="true" />
            </span>
          )}
        </li>
      </ul>
    </nav>
  );
}

export function Catalog({
  catalog,
  filters,
}: {
  catalog: CatalogPage;
  filters: CollectionFilters;
}) {
  const { items, total } = catalog;
  const pages = totalPages(total);
  const outOfRange = items.length === 0 && total > 0;
  const noun = total === 1 ? "object" : "objects";
  const status = `${total} ${noun}${pages > 1 && !outOfRange ? ` · Page ${filters.page} of ${pages}` : ""}`;
  const returnQuery = collectionQuery(filters);

  if (outOfRange) {
    return (
      <>
        <div className="my-5">
          <ResultsStatus>{status}</ResultsStatus>
        </div>
        <div className={stateLayout}>
          <h3>That page doesn’t exist.</h3>
          <p>
            This selection has {pages} {pages === 1 ? "page" : "pages"}. It may
            have changed since the link was shared.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <PageLink
              href={collectionHref({ ...filters, page: pages })}
              className="min-h-12"
            >
              Go to the last page
            </PageLink>
            <Link
              href={collectionHref({ ...filters, page: 1 })}
              className={buttonVariants({ variant: "outline" })}
            >
              Back to page one
            </Link>
          </div>
        </div>
      </>
    );
  }

  if (total === 0) {
    const filtered = hasActiveFilters(filters);
    return (
      <>
        <div className="my-5">
          <ResultsStatus>{status}</ResultsStatus>
        </div>
        <div className={stateLayout}>
          <h3>
            {filtered
              ? "No objects found."
              : "A little space for something new."}
          </h3>
          <p>
            {filtered
              ? "Try another search or clear your filters."
              : "The collection is empty. Please check back soon."}
          </p>
          {filtered && (
            <Link href="/#collection" className={buttonVariants()}>
              Clear filters
            </Link>
          )}
        </div>
      </>
    );
  }

  const first = catalog.skip + 1;
  return (
    <>
      <div className="my-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <ResultsStatus>{status}</ResultsStatus>
          {pages > 1 && (
            <p className="text-xs text-muted-foreground">
              Showing {first}–{Math.min(total, catalog.skip + items.length)}
            </p>
          )}
        </div>
        <ShareCollection
          key={collectionHref(filters)}
          href={collectionHref(filters)}
        />
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-8 lg:grid-cols-3 lg:gap-x-6 lg:gap-y-10">
        {items.map((product) => (
          <ProductCard
            key={product.id}
            product={product}
            returnQuery={returnQuery}
          />
        ))}
      </div>
      {total > pageSize && <Pagination filters={filters} pages={pages} />}
    </>
  );
}
