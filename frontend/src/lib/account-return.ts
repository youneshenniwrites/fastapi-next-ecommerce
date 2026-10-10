import {
  collectionQuery,
  parseCollection,
  type RawParams,
} from "@/lib/collection-url";

/** Matches the cart and database product id bound. */
const maxProductId = 2147483647;

export type AccountIntent = {
  /** Full navigation after a successful sign-in. */
  destination: string;
  /** Canonical login/register query, or empty when there is no product. */
  query: string;
};

export const collectionIntent: AccountIntent = {
  destination: "/#collection",
  query: "",
};

function values(input: RawParams, key: string): string[] {
  if (input instanceof URLSearchParams) return input.getAll(key);
  const value = Object.hasOwn(input, key) ? input[key] : undefined;
  if (value === undefined) return [];
  return Array.isArray(value) ? value : [value];
}

function productId(raw: string): number | null {
  if (!/^[1-9]\d{0,9}$/.test(raw)) return null;
  const id = Number(raw);
  if (!Number.isSafeInteger(id) || id < 1 || id > maxProductId) return null;
  return id;
}

function intentQuery(id: number, filtersQuery: string): string {
  return filtersQuery
    ? `?product=${id}&${filtersQuery.slice(1)}`
    : `?product=${id}`;
}

/**
 * A shopper returns to one local product plus recognised collection filters.
 * Open redirects, credentials and unrecognised parameters are discarded.
 */
export function accountIntent(input: RawParams): AccountIntent {
  const found = values(input, "product");
  if (found.length !== 1) return collectionIntent;
  const id = productId(found[0]);
  if (id === null) return collectionIntent;
  const filtersQuery = collectionQuery(parseCollection(input).filters);
  return {
    destination: `/products/${id}${filtersQuery}`,
    query: intentQuery(id, filtersQuery),
  };
}

/** Sign-in link for a catalog card or product page. Invalid ids use plain login. */
export function signInToAddHref(id: number, returnQuery = ""): string {
  if (productId(String(id)) === null) return "/login";
  const params = new URLSearchParams(
    returnQuery.startsWith("?") ? returnQuery.slice(1) : returnQuery,
  );
  params.set("product", String(id));
  return `/login${accountIntent(params).query}`;
}

function localProduct(destination: string): URL | null {
  let url: URL;
  try {
    url = new URL(destination, "https://vindor.local");
  } catch {
    return null;
  }
  if (
    url.origin !== "https://vindor.local" ||
    url.username ||
    url.password ||
    url.hash ||
    !/^\/products\/[1-9]\d{0,9}$/.test(url.pathname)
  )
    return null;
  return url;
}

/** Hard-navigation target. Anything off the allowlist returns to the collection. */
export function loginDestination(destination: string): string {
  if (destination === collectionIntent.destination) return destination;
  const url = localProduct(destination);
  if (!url) return collectionIntent.destination;
  const params = new URLSearchParams(url.search);
  params.set("product", url.pathname.slice("/products/".length));
  return accountIntent(params).destination;
}

/** Login or register href that keeps only a canonical product intent. */
export function accountHref(
  mode: "login" | "register",
  intent: AccountIntent,
): string {
  if (!intent.query) return `/${mode}`;
  const again = accountIntent(new URLSearchParams(intent.query.slice(1)));
  if (again.query !== intent.query) return `/${mode}`;
  return `/${mode}${intent.query}`;
}
