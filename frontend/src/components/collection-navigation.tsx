"use client";
import { useEffect, useRef } from "react";
import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Page links remount the results region. Remember that a link caused the
// navigation so focus lands on the new results instead of the document body.
let focusResults = false;

export function PageLink({
  href,
  current = false,
  className,
  children,
  ...props
}: {
  href: string;
  current?: boolean;
  className?: string;
  children: React.ReactNode;
} & Omit<React.ComponentProps<"a">, "href">) {
  return (
    <Link
      {...props}
      href={href}
      aria-current={current ? "page" : undefined}
      className={cn(
        buttonVariants({
          variant: current ? "default" : "outline",
          size: "lg",
        }),
        "min-h-11 min-w-11 px-3",
        className,
      )}
      onClick={() => {
        focusResults = true;
      }}
    >
      {children}
    </Link>
  );
}

export function ResultsStatus({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLParagraphElement>(null);
  useEffect(() => {
    if (!focusResults) return;
    focusResults = false;
    ref.current?.focus();
  }, []);
  return (
    <p
      ref={ref}
      role="status"
      tabIndex={-1}
      className="py-2 text-xs text-muted-foreground outline-none focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ring"
    >
      {children}
    </p>
  );
}
