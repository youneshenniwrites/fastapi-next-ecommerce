import { describe, expect, it } from "vitest";
import {
  collectionHref,
  collectionQuery,
  defaultFilters,
  maxPage,
  pageWindow,
  parseCollection,
  hasActiveFilters,
  skipForPage,
  sorts,
  totalPages,
} from "../src/lib/collection-url";

const parse = (query: string) => parseCollection(new URLSearchParams(query));

describe("collection URL parsing", () => {
  it("defaults an empty or unrelated query without complaint", () => {
    expect(parse("")).toEqual({ filters: defaultFilters, rejected: false });
    expect(parse("utm_source=news&next=https://evil.example")).toEqual({
      filters: defaultFilters,
      rejected: false,
    });
  });

  it("reads every recognised parameter", () => {
    expect(parse("q=%20oak%20&in_stock=1&sort=price-desc&page=3")).toEqual({
      filters: { query: "oak", inStock: true, sort: "price-desc", page: 3 },
      rejected: false,
    });
  });

  it("accepts every sort in the generated contract and nothing else", () => {
    expect(sorts.sort()).toEqual([
      "featured",
      "name",
      "price-asc",
      "price-desc",
    ]);
    for (const sort of sorts)
      expect(parse(`sort=${sort}`).filters.sort).toBe(sort);
    for (const sort of ["price", "__proto__", "constructor", "NAME", ""])
      expect(parse(`sort=${encodeURIComponent(sort)}`)).toMatchObject({
        filters: { sort: "featured" },
        rejected: true,
      });
  });

  it("rejects malformed pages and offsets beyond the API bound", () => {
    for (const page of [
      "0",
      "-1",
      "1.5",
      "01",
      "abc",
      "",
      "1e2",
      "99999",
      String(maxPage + 1),
    ])
      expect(parse(`page=${page}`)).toMatchObject({
        filters: { page: 1 },
        rejected: true,
      });
    expect(parse(`page=${maxPage}`).filters.page).toBe(maxPage);
    expect(skipForPage(maxPage)).toBeLessThanOrEqual(100000);
  });

  it("falls back for duplicate, oversized or NUL-containing parameters", () => {
    expect(parse("q=a&q=b")).toMatchObject({
      filters: { query: "" },
      rejected: true,
    });
    expect(parse("page=2&page=3").filters.page).toBe(1);
    expect(parse(`q=${"x".repeat(101)}`)).toMatchObject({
      filters: { query: "" },
      rejected: true,
    });
    expect(parse(`q=${"x".repeat(100)}`).filters.query).toHaveLength(100);
    expect(parse("q=a%00b")).toMatchObject({
      filters: { query: "" },
      rejected: true,
    });
    expect(parse("in_stock=yes")).toMatchObject({
      filters: { inStock: false },
      rejected: true,
    });
  });

  it("parses Next.js search parameter records, including arrays", () => {
    expect(parseCollection({ q: "lamp", page: "2" }).filters).toMatchObject({
      query: "lamp",
      page: 2,
    });
    expect(parseCollection({ q: ["a", "b"] }).rejected).toBe(true);
    expect(parseCollection({ q: undefined }).rejected).toBe(false);
    expect(parseCollection({ toString: "x", constructor: "y" }).rejected).toBe(
      false,
    );
  });
});

describe("canonical collection URLs", () => {
  it("omits defaults and orders parameters deterministically", () => {
    expect(collectionHref(defaultFilters)).toBe("/#collection");
    expect(
      collectionHref({
        page: 2,
        sort: "name",
        inStock: true,
        query: "desk mat",
      }),
    ).toBe("/?q=desk+mat&in_stock=1&sort=name&page=2#collection");
  });

  it("round-trips awkward search text through serialization", () => {
    for (const query of ["100% wool_", "a&b=c", "café ☕", "#hash?x", "日本"]) {
      const filters = { ...defaultFilters, query, page: 2 };
      const text = collectionQuery(filters);
      expect(parse(text.slice(1)).filters).toEqual(filters);
    }
  });

  it("never emits an external destination for hostile input", () => {
    const hostile = parse(
      "q=%2F%2Fevil.example&next=//evil.example&return=https://evil.example",
    );
    expect(collectionHref(hostile.filters)).toBe(
      "/?q=%2F%2Fevil.example#collection",
    );
    expect(collectionHref(hostile.filters).startsWith("/")).toBe(true);
  });
});

describe("pagination helpers", () => {
  it("counts at least one page", () => {
    expect([0, 1, 24, 25, 48, 49].map(totalPages)).toEqual([1, 1, 1, 2, 2, 3]);
  });

  it("shows every page when few and collapses long runs", () => {
    expect(pageWindow(1, 1)).toEqual([1]);
    expect(pageWindow(3, 7)).toEqual([1, 2, 3, 4, 5, 6, 7]);
    expect(pageWindow(1, 20)).toEqual([1, 2, 3, 4, null, 20]);
    expect(pageWindow(10, 20)).toEqual([1, null, 9, 10, 11, null, 20]);
    expect(pageWindow(20, 20)).toEqual([1, null, 17, 18, 19, 20]);
  });
});

describe("active filters", () => {
  it("ignores the page number but notices each recognised filter", () => {
    expect(hasActiveFilters(defaultFilters)).toBe(false);
    expect(hasActiveFilters({ ...defaultFilters, page: 3 })).toBe(false);
    expect(hasActiveFilters({ ...defaultFilters, query: "oak" })).toBe(true);
    expect(hasActiveFilters({ ...defaultFilters, inStock: true })).toBe(true);
    expect(hasActiveFilters({ ...defaultFilters, sort: "name" })).toBe(true);
  });
});
