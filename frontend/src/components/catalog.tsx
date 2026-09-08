"use client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  filterProducts,
  money,
  productArt,
  type Product,
  type Sort,
} from "@/lib/catalog";
export function Catalog({ products }: { products: Product[] }) {
  const [query, setQuery] = useState("");
  const [inStock, setInStock] = useState(false);
  const [sort, setSort] = useState<Sort>("featured");
  const visible = filterProducts(products, query, inStock, sort);
  return (
    <>
      <div className="catalog-tools">
        <label className="search">
          <span aria-hidden="true">⌕</span>
          <input
            type="search"
            aria-label="Search collection"
            placeholder="Find something for your space…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <label className="stock-filter">
          <input
            type="checkbox"
            checked={inStock}
            onChange={(e) => setInStock(e.target.checked)}
          />{" "}
          In stock only
        </label>
        <label className="sort">
          Sort by{" "}
          <select
            aria-label="Sort products"
            value={sort}
            onChange={(e) => setSort(e.target.value as Sort)}
          >
            <option value="featured">Featured</option>
            <option value="price-asc">Price: low to high</option>
            <option value="price-desc">Price: high to low</option>
            <option value="name">Name</option>
          </select>
        </label>
      </div>
      <p className="result-count" role="status">
        {visible.length} {visible.length === 1 ? "object" : "objects"}
        {products.length === 100
          ? " · Showing the first 100 catalog items"
          : ""}
      </p>
      {visible.length ? (
        <div className="product-grid">
          {visible.map((product) => (
            <article className="product" key={product.id}>
              <Link href={`/products/${product.id}`} className="product-link">
                <div className="product-image">
                  <Image
                    src={productArt(product.name)}
                    alt={`Illustration of ${product.name}`}
                    width={600}
                    height={500}
                  />
                  {product.stock === 0 && (
                    <Badge
                      variant="outline"
                      className="absolute top-4 left-4 rounded-none bg-background px-2.5 py-1 text-[9px] tracking-wide"
                    >
                      Out of stock
                    </Badge>
                  )}
                  <span className="product-arrow" aria-hidden="true">
                    ↗
                  </span>
                </div>
                <div className="product-meta">
                  <h3>{product.name}</h3>
                  <span>{money(product.price)}</span>
                </div>
                <p>
                  {product.description ||
                    "A considered object for your workspace."}
                </p>
              </Link>
            </article>
          ))}
        </div>
      ) : (
        <div className="state">
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
