"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  AlertTriangle,
  LoaderCircle,
  Minus,
  Plus,
  ShoppingBag,
  Trash2,
} from "lucide-react";
import { useCart, type CartItem } from "@/components/cart-provider";
import { ProductImage } from "@/components/product-image";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { money } from "@/lib/catalog";
import {
  cartQuantitySchema,
  type CartQuantityValues,
} from "@/lib/cart-validation";
import { cn } from "@/lib/utils";

function QuantityForm({ item }: { item: CartItem }) {
  const cart = useCart();
  const productId = item.product.id;
  const pending = Boolean(cart.pending[productId]);
  const error = cart.errors[productId];
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CartQuantityValues>({
    resolver: zodResolver(cartQuantitySchema),
    defaultValues: { quantity: item.quantity },
    mode: "onSubmit",
    reValidateMode: "onChange",
  });

  useEffect(() => {
    reset({ quantity: item.quantity });
  }, [item.quantity, reset]);

  async function submit(values: CartQuantityValues) {
    cart.clearError(productId);
    await cart.setQuantity(productId, values.quantity);
  }

  async function step(delta: -1 | 1) {
    cart.clearError(productId);
    await cart.stepQuantity(productId, delta);
  }

  const shortage = !item.available;
  const decreaseDisabled = pending || cart.readOnly || item.quantity <= 1;
  const increaseDisabled =
    pending || cart.readOnly || shortage || item.quantity >= 99;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="icon-sm"
          aria-label={`Decrease quantity of ${item.product.name}`}
          disabled={decreaseDisabled}
          onClick={() => void step(-1)}
        >
          <Minus aria-hidden="true" />
        </Button>
        <form
          noValidate
          aria-label={`Change quantity of ${item.product.name}`}
          onSubmit={(event) => {
            void handleSubmit(submit)(event);
          }}
          className="flex items-center gap-2"
        >
          <label htmlFor={`quantity-${productId}`} className="sr-only">
            Quantity of {item.product.name}, 1 to 99
          </label>
          <Input
            id={`quantity-${productId}`}
            {...register("quantity", { valueAsNumber: true })}
            inputMode="numeric"
            type="number"
            min={1}
            max={99}
            required
            disabled={pending || cart.readOnly}
            aria-invalid={Boolean(errors.quantity || error)}
            aria-describedby={
              errors.quantity || error
                ? `quantity-error-${productId}`
                : undefined
            }
            className="h-10 w-20 text-center"
          />
          <Button
            type="submit"
            variant="secondary"
            size="sm"
            disabled={pending || cart.readOnly}
            className="h-10"
          >
            {pending ? (
              <LoaderCircle
                className="size-4 animate-spin motion-reduce:animate-none"
                aria-hidden="true"
              />
            ) : (
              "Update"
            )}
          </Button>
        </form>
        <Button
          type="button"
          variant="outline"
          size="icon-sm"
          aria-label={`Increase quantity of ${item.product.name}`}
          disabled={increaseDisabled}
          onClick={() => void step(1)}
        >
          <Plus aria-hidden="true" />
        </Button>
      </div>
      {(errors.quantity || error) && (
        <p
          id={`quantity-error-${productId}`}
          role="alert"
          className="text-xs text-destructive"
        >
          {errors.quantity
            ? "Quantity must be a whole number from 1 to 99."
            : error}
        </p>
      )}
      {shortage && (
        <p
          role="note"
          className="flex items-start gap-1.5 text-xs text-muted-foreground"
        >
          <AlertTriangle
            className="mt-0.5 size-3.5 shrink-0"
            aria-hidden="true"
          />
          Not enough stock for more. You can keep or reduce this quantity.
        </p>
      )}
    </div>
  );
}

function CartLine({ item }: { item: CartItem }) {
  const cart = useCart();
  const pending = Boolean(cart.pending[item.product.id]);
  return (
    <li className="grid gap-4 border border-border bg-background p-4 sm:grid-cols-[112px_1fr_auto] sm:gap-6 sm:p-5">
      <div className="overflow-hidden bg-muted">
        <ProductImage name={item.product.name} />
      </div>
      <div className="min-w-0">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <h2 className="text-sm font-medium leading-snug [overflow-wrap:anywhere]">
            <Link
              href={`/products/${item.product.id}`}
              className="hover:underline underline-offset-4"
            >
              {item.product.name}
            </Link>
          </h2>
          <p className="text-sm font-medium">{money(item.line_total)}</p>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          {money(item.product.price)} each · GBP
        </p>
        {!item.available && (
          <Badge variant="outline" className="mt-3">
            <AlertTriangle className="size-3.5" aria-hidden="true" />
            Limited stock
          </Badge>
        )}
        <div className="mt-4">
          <QuantityForm item={item} />
        </div>
      </div>
      <div className="flex sm:flex-col sm:items-end sm:justify-between">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={pending || cart.readOnly}
          onClick={() => void cart.removeItem(item.product.id)}
          aria-label={`Remove ${item.product.name} from cart`}
        >
          <Trash2 aria-hidden="true" />
          Remove
        </Button>
        <p className="ml-auto text-xs text-muted-foreground sm:ml-0">
          Qty {item.quantity}
        </p>
      </div>
    </li>
  );
}

export function CartView() {
  const cart = useCart();

  if (cart.state.status === "loading") {
    return (
      <div role="status" aria-label="Loading your cart" className="space-y-4">
        <span className="sr-only">Loading your cart…</span>
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (cart.state.status === "guest") {
    return (
      <section aria-label="Sign in to view your cart" className="space-y-5">
        <ShoppingBag className="size-7 text-primary" aria-hidden="true" />
        <h2 className="text-xl">Sign in to view your saved cart</h2>
        <p className="text-sm text-muted-foreground">
          Your session may have expired. Sign in to restore your saved objects.
        </p>
        <Button asChild>
          <Link href="/login" prefetch={false}>
            Sign in
          </Link>
        </Button>
      </section>
    );
  }

  if (cart.state.status === "error") {
    return (
      <section aria-label="Cart unavailable" className="space-y-5">
        <p role="alert">
          Your cart is temporarily unavailable. Please try again.
        </p>
        <Button onClick={() => cart.refresh()}>Try again</Button>
      </section>
    );
  }

  if (cart.state.cart.items.length === 0) {
    return (
      <section aria-label="Empty cart" className="space-y-5">
        <ShoppingBag className="size-7 text-primary" aria-hidden="true" />
        <h2 className="text-xl">Your cart is empty</h2>
        <p className="text-sm text-muted-foreground">
          Browse the collection and save objects to see them here.
        </p>
        <Link
          href="/#collection"
          className={cn(buttonVariants(), "inline-flex")}
        >
          Explore the collection
        </Link>
      </section>
    );
  }

  const { cart: data } = cart.state;
  return (
    <div className="space-y-8">
      <p role="status" className="text-xs text-muted-foreground">
        {data.items.length} {data.items.length === 1 ? "line" : "lines"} ·{" "}
        {data.items.reduce((total, item) => total + item.quantity, 0)} objects
      </p>
      <ul className="space-y-4">
        {data.items.map((item) => (
          <CartLine key={item.product.id} item={item} />
        ))}
      </ul>
      <section
        aria-label="Cart summary"
        className="rounded-md border border-border bg-secondary p-5 sm:p-6"
      >
        <div className="flex items-baseline justify-between gap-4">
          <h2 className="text-sm font-medium">Subtotal</h2>
          <p className="text-xl font-semibold" data-testid="cart-subtotal">
            {money(data.subtotal)}{" "}
            <span className="text-xs font-normal">GBP</span>
          </p>
        </div>
        <p className="mt-3 text-xs leading-5 text-muted-foreground">
          Prices are current backend prices and can change. Adding objects does
          not reserve stock; availability is checked again at checkout.
        </p>
      </section>
    </div>
  );
}
