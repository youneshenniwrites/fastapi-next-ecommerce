import { cn } from "@/lib/utils";
export const container =
  "mx-auto w-full max-w-[1440px] px-5 sm:px-8 lg:px-[5%]";
export const eyebrow = "mb-5 text-[10px] font-semibold tracking-[0.18em]";
export const stateLayout =
  "px-5 py-16 text-center [&_h1]:font-serif [&_h1]:text-3xl [&_h3]:font-serif [&_h3]:text-3xl [&_p]:my-6 [&_p]:text-muted-foreground";
export function SectionHeading({
  eyebrow: label,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className={cn(eyebrow, "mb-3")}>{label}</p>
        <h2 className="font-serif text-4xl leading-tight tracking-tight sm:text-[42px]">
          {title}
        </h2>
      </div>
      <p className="text-xs text-muted-foreground">{description}</p>
    </div>
  );
}
