"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { collectionHref, parseCollection } from "@/lib/collection-url";

export function CollectionBackLink() {
  const { filters } = parseCollection(useSearchParams());
  return (
    <Link
      className="mb-8 inline-flex items-center gap-2 text-sm hover:underline"
      href={collectionHref(filters)}
    >
      <ArrowLeft className="size-4" aria-hidden="true" /> Back to the collection
    </Link>
  );
}
