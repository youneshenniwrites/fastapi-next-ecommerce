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
const artwork: Record<string, string> = {
  "Oak Monitor Stand": "stand",
  "Felt Desk Mat": "mat",
  "Task Light": "lamp",
  "Cable Tray": "tray",
  "Notebook Set": "notebooks",
  "Ceramic Pen Cup": "cup",
  "Compact Keyboard": "keyboard",
  "Focus Headphones": "headphones",
  "Insulated Bottle": "bottle",
  "Handled Planter": "planter",
  "Analogue Desk Clock": "clock",
  "Wireless Mouse": "mouse",
};
export function productArt(name: string) {
  return Object.hasOwn(artwork, name)
    ? `/photos/${artwork[name]}.webp`
    : undefined;
}
