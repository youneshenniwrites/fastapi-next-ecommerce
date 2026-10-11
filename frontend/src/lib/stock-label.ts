export function stockLabel(stock: number): string {
  if (stock < 1) return "Out of stock";
  if (stock === 1) return "1 in stock";
  return `${stock} in stock`;
}
