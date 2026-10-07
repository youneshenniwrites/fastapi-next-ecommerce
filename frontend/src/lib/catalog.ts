import type { components } from "./api/schema";
export type Product = components["schemas"]["ProductRead"];
export function priceInPence(value: string): bigint {
  if (!/^\d+\.\d{2}$/.test(value)) throw new Error("Invalid GBP price");
  return BigInt(value.replace(".", ""));
}
export function money(value: string): string {
  const pence = priceInPence(value);
  return `£${(pence / 100n).toLocaleString("en-GB")}.${(pence % 100n).toString().padStart(2, "0")}`;
}
/** Keep in step with backend/app/catalog_media.py IMAGE_KEYS. */
export const imageKeys = [
  "stand",
  "mat",
  "lamp",
  "tray",
  "notebooks",
  "cup",
  "keyboard",
  "headphones",
  "bottle",
  "planter",
  "clock",
  "mouse",
] as const;
const allowlisted = new Set<string>(imageKeys);
export function productArt(key: string | null | undefined) {
  return key && allowlisted.has(key) ? `/photos/${key}.webp` : undefined;
}
