import { ProductImage } from "@/components/product-image";
import Link from "next/link";
import { ArrowLeft, Check, Minus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { container, eyebrow } from "@/components/storefront-layout";
import { cn } from "@/lib/utils";
import { money, type Product } from "@/lib/catalog";
import { AddToCartButton } from "@/components/add-to-cart-button";
export function ProductDetails({ product }: { product: Product }) {
  return (
    <main id="main" className={cn(container, "py-10 pb-20")}>
      <Link
        className="mb-8 inline-flex items-center gap-2 text-sm hover:underline"
        href="/#collection"
      >
        <ArrowLeft className="size-4" aria-hidden="true" /> Back to the
        collection
      </Link>
      <div className="grid items-start gap-8 md:grid-cols-2 lg:gap-16">
        <div className="overflow-hidden bg-muted">
          <ProductImage name={product.name} priority />
        </div>
        <div className="min-w-0 py-4">
          <p className={eyebrow}>THE WORKSPACE COLLECTION</p>
          <h1 className="mb-6 [overflow-wrap:anywhere] font-serif text-4xl leading-tight tracking-tight lg:text-5xl">
            {product.name}
          </h1>
          <p className="detail-price mb-6 text-2xl">
            {money(product.price)}{" "}
            <span className="ml-2 text-xs text-muted-foreground">GBP</span>
          </p>
          <p className="text-sm leading-7 text-muted-foreground [overflow-wrap:anywhere]">
            {product.description}
          </p>
          <Badge variant="secondary" className="mt-6 gap-2 px-3 py-1.5">
            {product.stock ? (
              <Check className="size-3.5" aria-hidden="true" />
            ) : (
              <Minus className="size-3.5" aria-hidden="true" />
            )}
            {product.stock ? "In stock" : "Out of stock"}
          </Badge>
          <div className="mt-8">
            <AddToCartButton product={product} />
          </div>
          <div className="mt-8 border border-border p-5 text-sm [&_p]:mt-2 [&_p]:text-muted-foreground">
            <strong>Saved to your account.</strong>
            <p>
              Signed-in carts persist across visits. Prices are current backend
              prices and can change; adding objects does not reserve stock.
              Checkout is coming next; no purchases can be made yet. Photography
              shows representative workspace objects, not exact products or
              brand endorsements.
            </p>
          </div>
          <dl className="mt-8 text-xs [&_div]:flex [&_div]:justify-between [&_div]:gap-4 [&_div]:border-b [&_div]:border-border [&_div]:py-3">
            <div>
              <dt>Collection</dt>
              <dd>Everyday focus</dd>
            </div>
            <div>
              <dt>Reference</dt>
              <dd>VINDOR / {String(product.id).padStart(3, "0")}</dd>
            </div>
          </dl>
        </div>
      </div>
    </main>
  );
}
