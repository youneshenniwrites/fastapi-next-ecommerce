import { ProductImage } from "@/components/product-image";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { money, type Product } from "@/lib/catalog";
import { AddToCartButton } from "@/components/add-to-cart-button";
export function ProductCard({ product }: { product: Product }) {
  return (
    <article className="product min-w-0">
      <Link href={`/products/${product.id}`} className="group block">
        <div className="relative overflow-hidden bg-muted">
          <ProductImage name={product.name} />
          {product.stock === 0 && (
            <Badge
              variant="outline"
              className="absolute left-3 top-3 rounded-none bg-background px-2 py-1 text-[10px]"
            >
              Out of stock
            </Badge>
          )}
          <span className="absolute bottom-3 right-3 grid size-8 place-items-center rounded-full bg-background/90">
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </span>
        </div>
        <div className="mt-4 flex flex-col gap-1 lg:flex-row lg:justify-between lg:gap-3">
          <h3 className="text-sm font-medium leading-snug [overflow-wrap:anywhere]">
            {product.name}
          </h3>
          <span className="whitespace-nowrap text-xs">
            {money(product.price)}
          </span>
        </div>
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground [overflow-wrap:anywhere]">
          {product.description || "A considered object for your workspace."}
        </p>
      </Link>
      <div className="mt-3">
        <AddToCartButton product={product} compact />
      </div>
    </article>
  );
}
