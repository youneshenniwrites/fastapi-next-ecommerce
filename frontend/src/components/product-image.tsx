import Image from "next/image";
import { ImageOff } from "lucide-react";
import { productArt, type Product } from "@/lib/catalog";
export function ProductImage({
  image,
  priority = false,
}: {
  image: Product["image"];
  priority?: boolean;
}) {
  const src = productArt(image?.key);
  if (!src || !image)
    return (
      <div
        className="grid aspect-[6/5] place-items-center bg-muted text-muted-foreground"
        role="img"
        aria-label="Product photograph unavailable"
      >
        <ImageOff className="size-10" aria-hidden="true" />
      </div>
    );
  return (
    <Image
      className="aspect-[6/5] w-full object-cover transition-transform duration-300 group-hover:scale-[1.03] motion-reduce:transform-none"
      src={src}
      alt={image.alt}
      width={1200}
      height={1000}
      sizes={
        priority
          ? "(min-width: 768px) 50vw, 100vw"
          : "(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
      }
      priority={priority}
    />
  );
}
