"use client";
import { useState } from "react";
import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  NativeSelect,
  NativeSelectOption,
} from "@/components/ui/native-select";
import { ProductCard } from "@/components/product-card";
import { stateLayout } from "@/components/storefront-layout";
import { filterProducts, type Product, type Sort } from "@/lib/catalog";
export function Catalog({ products }: { products: Product[] }) {
  const [query, setQuery] = useState("");
  const [inStock, setInStock] = useState(false);
  const [sort, setSort] = useState<Sort>("featured");
  const visible = filterProducts(products, query, inStock, sort);
  return (
    <>
      <div className="flex flex-wrap items-center gap-4 border-y border-border py-4">
        <div className="relative min-w-0 basis-full md:flex-1 md:basis-auto">
          <Search
            className="pointer-events-none absolute left-3 top-3 size-4 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            className="h-10 pl-10"
            type="search"
            aria-label="Search collection"
            placeholder="Find something for your space…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <div className="flex min-h-11 items-center gap-2">
          <Checkbox
            id="in-stock"
            checked={inStock}
            onCheckedChange={(checked) => setInStock(checked === true)}
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
          <label htmlFor="sort-products" className="text-xs">
            Sort by
          </label>
          <NativeSelect
            id="sort-products"
            aria-label="Sort products"
            className="h-10 max-w-[180px]"
            value={sort}
            onChange={(e) => setSort(e.target.value as Sort)}
          >
            <NativeSelectOption value="featured">Featured</NativeSelectOption>
            <NativeSelectOption value="price-asc">
              Price: low to high
            </NativeSelectOption>
            <NativeSelectOption value="price-desc">
              Price: high to low
            </NativeSelectOption>
            <NativeSelectOption value="name">Name</NativeSelectOption>
          </NativeSelect>
        </div>
      </div>
      <p role="status" className="my-5 text-xs text-muted-foreground">
        {visible.length} {visible.length === 1 ? "object" : "objects"}
        {products.length === 100
          ? " · Showing the first 100 catalog items"
          : ""}
      </p>
      {visible.length ? (
        <div className="grid grid-cols-2 gap-x-4 gap-y-8 lg:grid-cols-3 lg:gap-x-6 lg:gap-y-10">
          {visible.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      ) : (
        <div className={stateLayout}>
          <h3>
            {products.length
              ? "No objects found."
              : "A little space for something new."}
          </h3>
          <p>
            {products.length
              ? "Try another search or clear your filters."
              : "The collection is empty. Please check back soon."}
          </p>
          {products.length > 0 && (
            <Button
              onClick={() => {
                setQuery("");
                setInStock(false);
              }}
            >
              Clear filters
            </Button>
          )}
        </div>
      )}
    </>
  );
}
