import { notFound } from "next/navigation";
import { apiClient } from "@/lib/api/client";
import { ProductDetails } from "@/components/product-details";
import { collectionHref, parseCollection } from "@/lib/collection-url";
export const dynamic = "force-dynamic";
export default async function ProductPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { id } = await params;
  if (!/^\d+$/.test(id) || !Number.isSafeInteger(Number(id)) || Number(id) < 1)
    notFound();
  const { data, response } = await apiClient().GET(
    "/api/v1/products/{product_id}",
    { params: { path: { product_id: Number(id) } } },
  );
  if (response.status === 404) notFound();
  if (!data || !response.ok) throw new Error("Product unavailable");
  const { filters } = parseCollection(await searchParams);
  return (
    <ProductDetails product={data} collectionHref={collectionHref(filters)} />
  );
}
