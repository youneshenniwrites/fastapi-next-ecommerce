import type { paths } from "@/lib/api/schema";

type SearchQuery = NonNullable<
  paths["/api/v1/products/search"]["get"]["parameters"]["query"]
>;

/** Allowlisted sort literals come from the generated FastAPI contract. */
export type Sort = NonNullable<SearchQuery["sort"]>;

export const sortLabels: Record<Sort, string> = {
  featured: "Featured",
  "price-asc": "Price: low to high",
  "price-desc": "Price: high to low",
  name: "Name",
};
export const sorts = Object.keys(sortLabels) as Sort[];

export const pageSize = 24;
export const maxQueryLength = 100;
const maxSkip = 100000;
export const maxPage = Math.floor(maxSkip / pageSize) + 1;

export type CollectionFilters = {
  query: string;
  inStock: boolean;
  sort: Sort;
  page: number;
  /** Stored category slug. Empty means All, which is not a category. */
  category: string;
};

export const defaultFilters: CollectionFilters = {
  query: "",
  inStock: false,
  sort: "featured",
  page: 1,
  category: "",
};

const categorySlug = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

export type RawParams =
  URLSearchParams | Record<string, string | string[] | undefined>;

function values(input: RawParams, key: string): string[] {
  if (input instanceof URLSearchParams) return input.getAll(key);
  const value = Object.hasOwn(input, key) ? input[key] : undefined;
  if (value === undefined) return [];
  return Array.isArray(value) ? value : [value];
}

function isSort(value: string): value is Sort {
  return Object.hasOwn(sortLabels, value);
}

/**
 * Parse public collection parameters. Unknown parameters are ignored; a
 * recognised parameter that is duplicated, oversized or invalid falls back to
 * its default and sets `rejected` so the page can explain the reset.
 */
export function parseCollection(input: RawParams): {
  filters: CollectionFilters;
  rejected: boolean;
} {
  const filters: CollectionFilters = { ...defaultFilters };
  let rejected = false;
  function single(key: string): string | undefined {
    const found = values(input, key);
    if (found.length === 0) return undefined;
    if (found.length > 1) {
      rejected = true;
      return undefined;
    }
    return found[0];
  }

  const query = single("q");
  if (query !== undefined) {
    const trimmed = query.trim();
    if (trimmed.length > maxQueryLength || trimmed.includes("\u0000"))
      rejected = true;
    else filters.query = trimmed;
  }
  const stock = single("in_stock");
  if (stock !== undefined) {
    if (stock === "1") filters.inStock = true;
    else if (stock !== "0") rejected = true;
  }
  const sort = single("sort");
  if (sort !== undefined) {
    if (isSort(sort)) filters.sort = sort;
    else rejected = true;
  }
  const page = single("page");
  if (page !== undefined) {
    if (/^[1-9]\d{0,3}$/.test(page) && Number(page) <= maxPage)
      filters.page = Number(page);
    else rejected = true;
  }
  const category = single("category");
  if (category !== undefined) {
    if (category.length <= 64 && categorySlug.test(category))
      filters.category = category;
    else rejected = true;
  }
  return { filters, rejected };
}

/** Canonical query string: recognised, non-default parameters in fixed order. */
export function collectionQuery(filters: CollectionFilters): string {
  const params = new URLSearchParams();
  if (filters.category) params.set("category", filters.category);
  if (filters.query) params.set("q", filters.query);
  if (filters.inStock) params.set("in_stock", "1");
  if (filters.sort !== defaultFilters.sort) params.set("sort", filters.sort);
  if (filters.page > 1) params.set("page", String(filters.page));
  const text = params.toString();
  return text ? `?${text}` : "";
}

export function collectionHref(filters: CollectionFilters): string {
  return `/${collectionQuery(filters)}#collection`;
}

export function hasActiveFilters(filters: CollectionFilters): boolean {
  return (
    filters.query !== "" ||
    filters.inStock ||
    filters.sort !== defaultFilters.sort ||
    filters.category !== ""
  );
}

export function skipForPage(page: number): number {
  return (page - 1) * pageSize;
}

export function totalPages(total: number): number {
  return Math.max(1, Math.ceil(total / pageSize));
}

/** Page numbers to show, with null marking a collapsed run. */
export function pageWindow(page: number, pages: number): (number | null)[] {
  if (pages <= 7) return Array.from({ length: pages }, (_, index) => index + 1);
  const wanted = new Set([1, pages, page - 1, page, page + 1]);
  if (page <= 3) [2, 3, 4].forEach((n) => wanted.add(n));
  if (page >= pages - 2)
    [pages - 3, pages - 2, pages - 1].forEach((n) => wanted.add(n));
  const sorted = [...wanted]
    .filter((n) => n >= 1 && n <= pages)
    .sort((a, b) => a - b);
  const result: (number | null)[] = [];
  sorted.forEach((n, index) => {
    if (index > 0 && n - sorted[index - 1] > 1) result.push(null);
    result.push(n);
  });
  return result;
}
