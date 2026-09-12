// Per-owner admission guard only; Next owns action dispatch and server data.
export class CartOperations {
  private active = new Map<number, symbol>();
  constructor(private owner: string | null) {}
  reset(owner: string | null) {
    if (owner !== this.owner) {
      this.owner = owner;
      this.active.clear();
    }
  }
  begin(productId: number) {
    if (this.active.has(productId)) return null;
    const operation = Symbol();
    this.active.set(productId, operation);
    return operation;
  }
  current(productId: number, operation: symbol) {
    return this.active.get(productId) === operation;
  }
  finish(productId: number, operation: symbol) {
    if (!this.current(productId, operation)) return false;
    this.active.delete(productId);
    return true;
  }
}
