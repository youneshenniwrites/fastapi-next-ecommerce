import type { components } from "./api/schema";
export type Product = components["schemas"]["ProductRead"];
export type Sort = "featured" | "price-asc" | "price-desc" | "name";
export function priceInPence(value: string): bigint {
  if (!/^\d+\.\d{2}$/.test(value)) throw new Error("Invalid GBP price");
  return BigInt(value.replace(".", ""));
}
export function money(value: string): string {
  const pence = priceInPence(value);
  return `£${(pence / 100n).toLocaleString("en-GB")}.${(pence % 100n).toString().padStart(2, "0")}`;
}
export function filterProducts(
  products: Product[],
  query: string,
  inStock: boolean,
  sort: Sort,
) {
  const result = products.filter(
    (p) =>
      p.name.toLowerCase().includes(query.trim().toLowerCase()) &&
      (!inStock || p.stock > 0),
  );
  return result.sort((a, b) => {
    if (sort === "name") return a.name.localeCompare(b.name, "en-GB");
    if (sort === "featured") return a.id - b.id;
    const left = priceInPence(a.price),
      right = priceInPence(b.price);
    const order = left < right ? -1 : left > right ? 1 : 0;
    return sort === "price-desc" ? -order : order;
  });
}
const artwork: Record<string, string> = {
  "Oak Monitor Stand": "stand",
  "Felt Desk Mat": "mat",
  "Task Light": "lamp",
  "Cable Tray": "tray",
  "Notebook Set": "notebooks",
  "Ceramic Pen Cup": "cup",
};
export function productArt(name: string) {
  return Object.hasOwn(artwork, name)
    ? `/photos/${artwork[name]}.webp`
    : undefined;
}
