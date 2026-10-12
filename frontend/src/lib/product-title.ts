export function catalogProductId(id: string): number | null {
  if (!/^\d+$/.test(id) || !Number.isSafeInteger(Number(id)) || Number(id) < 1)
    return null;
  return Number(id);
}

export function productDocumentTitle(name: string | null | undefined): string {
  const trimmed = name?.trim() ?? "";
  return trimmed.length > 0 ? trimmed : "Not found";
}
