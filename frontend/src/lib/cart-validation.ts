import { z } from "zod";

export const cartQuantitySchema = z.object({
  quantity: z.number().int().min(1).max(99),
});

export type CartQuantityValues = z.infer<typeof cartQuantitySchema>;
