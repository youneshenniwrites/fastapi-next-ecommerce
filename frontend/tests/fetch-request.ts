/** Inspect either public fetch form as the effective wire request. */
export function fetchRequest([input, init]: Parameters<typeof fetch>) {
  return new Request(input, init);
}
