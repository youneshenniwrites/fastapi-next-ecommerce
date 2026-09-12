import { CartProvider } from "@/components/cart-provider";
import { readCartSnapshot } from "@/lib/cart-data";
import { CartView } from "@/components/cart-view";
import { container, eyebrow } from "@/components/storefront-layout";
import { cn } from "@/lib/utils";

export const metadata = {
  title: "Your cart",
  robots: { index: false, follow: false },
};

export default async function Page() {
  const snapshot = await readCartSnapshot();
  return (
    <main id="main" className={cn(container, "py-10 pb-20")}>
      <p className={eyebrow}>YOUR VINDOR CART</p>
      <h1 className="mb-6 font-serif text-4xl leading-tight tracking-tight lg:text-5xl">
        Your cart.
      </h1>
      <p className="mb-8 max-w-md text-sm leading-7 text-muted-foreground">
        Saved to your account. Prices are current and stock is not reserved.
      </p>
      <CartProvider key={snapshot.owner ?? snapshot.status} snapshot={snapshot}>
        <CartView />
      </CartProvider>
    </main>
  );
}
