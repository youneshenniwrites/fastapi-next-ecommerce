import { cache } from "react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { apiClient } from "@/lib/api/client";
import { ProductDetails } from "@/components/product-details";
import { parseCollection } from "@/lib/collection-url";
import { catalogProductId, productDocumentTitle } from "@/lib/product-title";

export const dynamic = "force-dynamic";

const readCatalogProduct = cache(async (id: string) => {
  const productId = catalogProductId(id);
  if (productId === null) return null;
  const { data, response } = await apiClient().GET(
    "/api/v1/products/{product_id}",
    { params: { path: { product_id: productId } } },
  );
  if (response.status === 404) return null;
  if (!data || !response.ok) throw new Error("Product unavailable");
  return data;
});

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const product = await readCatalogProduct((await params).id);
  return { title: productDocumentTitle(product?.name) };
}

export default async function ProductPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const product = await readCatalogProduct((await params).id);
  if (!product) notFound();
  const { filters } = parseCollection(await searchParams);
  return <ProductDetails product={product} filters={filters} />;
}
