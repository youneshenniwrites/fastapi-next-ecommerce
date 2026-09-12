import { Suspense } from "react";
import { CatalogSkeleton } from "@/components/catalog-skeleton";
import { ArrowUpRight, Minus } from "lucide-react";
import {
  container,
  eyebrow,
  stateLayout,
  SectionHeading,
} from "@/components/storefront-layout";
import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/button";
import { RetryCatalog } from "@/components/retry-catalog";
import Image from "next/image";
import { apiClient } from "@/lib/api/client";
import { Catalog } from "@/components/catalog";
export const dynamic = "force-dynamic";
export default function Home() {
  return (
    <main id="main">
      <section
        className={cn(
          container,
          "grid items-center gap-8 py-10 sm:grid-cols-2 lg:gap-12 lg:py-14",
        )}
      >
        <div className="min-w-0">
          <p className={eyebrow}>THE ART OF WORKING WELL</p>
          <h1 className="mb-6 font-serif text-[clamp(40px,5vw,70px)] leading-[1.1] tracking-[-0.04em]">
            Room to think.
            <br />
            <em>Space to create.</em>
          </h1>
          <p className="mb-8 max-w-sm text-sm leading-8 text-muted-foreground">
            Thoughtful objects for the place you do your best work. Simple
            forms. A calmer everyday.
          </p>
          <a className={buttonVariants()} href="#collection">
            Explore the collection{" "}
            <ArrowUpRight aria-hidden="true" className="size-4" />
          </a>
          <div className="mt-9 flex items-center gap-3 text-[10px] text-muted-foreground">
            <Minus className="size-6" aria-hidden="true" /> A considered
            workspace starts with less.
          </div>
        </div>
        <div className="relative overflow-hidden bg-muted">
          <Image
            className="aspect-[15/13] w-full object-cover"
            src="/photos/workspace.webp"
            alt="Workspace with a monitor, laptop, wooden accessories and plants"
            width={900}
            height={780}
            priority
          />
          <div className="absolute inset-x-5 bottom-5 flex justify-between bg-background/95 p-3 text-[8px] tracking-widest">
            <span>THE EVERYDAY EDIT</span>
            <span>01 / 12</span>
          </div>
        </div>
      </section>
      <section
        id="collection"
        className={cn(container, "border-t border-border py-12 sm:py-16")}
      >
        <SectionHeading
          eyebrow="LESS, BUT BETTER"
          title="Find your focus."
          description="Small details. A different kind of day."
        />
        <Suspense fallback={<CatalogSkeleton />}>
          <CatalogData />
        </Suspense>
      </section>
      <section
        id="approach"
        className="relative overflow-hidden bg-secondary px-5 py-12 sm:px-8 sm:py-16 lg:px-[max(5%,calc((100%-1296px)/2))]"
      >
        <p className={eyebrow}>OUR APPROACH</p>
        <h2 className="font-serif text-4xl leading-tight tracking-tight sm:text-[45px]">
          A place for everything.
          <br />
          <em>More space for you.</em>
        </h2>
        <p className="mt-6 max-w-md text-sm leading-7 text-muted-foreground">
          VINDOR explores a simple idea: a workspace should make room for your
          attention. This fictional collection brings warm textures and useful
          forms into everyday focus.
        </p>
        <span
          className="absolute right-[12%] top-0 hidden font-serif text-[250px] leading-none text-muted-foreground lg:block"
          aria-hidden="true"
        >
          v.
        </span>
      </section>
    </main>
  );
}

async function CatalogData() {
  let products;
  try {
    const result = await apiClient().GET("/api/v1/products/", {
      params: { query: { limit: 100, skip: 0 } },
    });
    if (result.error || !result.data) throw new Error("Catalog unavailable");
    products = result.data;
  } catch {
    products = null;
  }
  return products === null ? (
    <div className={stateLayout} role="alert" aria-label="Catalog unavailable">
      <h3>The collection is taking a moment.</h3>
      <p>We couldn’t reach the catalog. Please try again shortly.</p>
      <RetryCatalog />
    </div>
  ) : (
    <Catalog products={products} />
  );
}
