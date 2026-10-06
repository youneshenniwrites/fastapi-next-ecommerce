// @vitest-environment jsdom
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

vi.mock("../src/components/add-to-cart-button", () => ({
  AddToCartButton: () => null,
}));
import { Catalog } from "../src/components/catalog";
import { CategoryNav } from "../src/components/category-nav";
import { ProductDetails } from "../src/components/product-details";
import {
  defaultFilters,
  type CollectionFilters,
} from "../src/lib/collection-url";
import type { Product } from "../src/lib/catalog";

afterEach(cleanup);

const filters: CollectionFilters = {
  ...defaultFilters,
  query: "oak",
  inStock: true,
  sort: "name",
  page: 3,
};

it("resets the page when a category link is chosen and keeps the other filters", () => {
  render(
    <CategoryNav
      filters={filters}
      categories={[
        { slug: "lighting", name: "Lighting", count: 1 },
        { slug: "uncategorized", name: "Uncategorized", count: 0 },
      ]}
    />,
  );
  expect(
    screen.getByRole("link", { name: "All, 1 object" }).getAttribute("href"),
  ).toBe("/?q=oak&in_stock=1&sort=name#collection");
  const lighting = screen.getByRole("link", { name: "Lighting, 1 object" });
  expect(lighting.getAttribute("href")).toBe(
    "/?category=lighting&q=oak&in_stock=1&sort=name#collection",
  );
  expect(lighting.getAttribute("aria-current")).toBeNull();
});

it("marks the selected category and describes an empty category", () => {
  render(
    <CategoryNav
      filters={{ ...defaultFilters, category: "uncategorized" }}
      categories={[{ slug: "uncategorized", name: "Uncategorized", count: 0 }]}
    />,
  );
  expect(
    screen
      .getByRole("link", { name: "Uncategorized, 0 objects" })
      .getAttribute("aria-current"),
  ).toBe("page");
});

it("explains an empty category without calling it a failed search", () => {
  render(
    <Catalog
      filters={{ ...defaultFilters, category: "workspace-comforts" }}
      catalog={{ items: [], total: 0, limit: 24, skip: 0 }}
    />,
  );
  expect(
    screen.getByRole("heading", { name: "Nothing in this category yet." }),
  ).toBeTruthy();
  expect(
    screen.queryByRole("heading", { name: "No objects found." }),
  ).toBeNull();
});

const product: Product = {
  id: 3,
  name: "Task Light",
  description: "Fictional lamp",
  price: "65.00",
  currency: "GBP",
  stock: 8,
  category: { slug: "lighting", name: "Lighting" },
};

it("shows the product category instead of a fixed collection label", () => {
  render(
    <ProductDetails
      product={product}
      filters={{
        ...defaultFilters,
        category: "desk-organization",
        query: "oak",
      }}
    />,
  );
  expect(screen.queryByText("Everyday focus")).toBeNull();
  const categoryLinks = screen.getAllByRole("link", { name: "Lighting" });
  expect(categoryLinks).toHaveLength(2);
  for (const link of categoryLinks) {
    expect(link.getAttribute("href")).toBe(
      "/?category=lighting&q=oak#collection",
    );
  }
  expect(
    screen
      .getByRole("link", { name: "Back to the collection" })
      .getAttribute("href"),
  ).toBe("/?category=desk-organization&q=oak#collection");
  expect(screen.getByRole("navigation", { name: "Breadcrumb" })).toBeTruthy();
});
