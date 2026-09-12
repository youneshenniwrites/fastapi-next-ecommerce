import type { components } from "./api/schema";

export type Cart = components["schemas"]["CartRead"];
export type CartItem = components["schemas"]["CartItem"];
export type CartSnapshot =
  | { status: "guest"; owner: null }
  | { status: "error"; owner: string | null }
  | { status: "ready"; owner: string; cart: Cart };
export type CartChange =
  | { kind: "set"; productId: number; quantity: number }
  | { kind: "add"; productId: number }
  | { kind: "remove"; productId: number };
export type CartFailure = { error: string; uncertain?: true };
export type CartActionResult = { ok: true } | ({ ok: false } & CartFailure);
