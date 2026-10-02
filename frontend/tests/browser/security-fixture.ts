import { test as base, expect } from "@playwright/test";

type Violation = { directive: string; disposition: string };
export const test = base.extend<{
  allowCspViolations: boolean;
  cspViolations: Violation[];
}>({
  allowCspViolations: [false, { option: true }],
  cspViolations: [
    async ({ context, allowCspViolations }, use) => {
      const violations: Violation[] = [];
      // Record only directive/disposition, never private URLs or script samples.
      await context.exposeBinding("recordPolicyViolation", (_source, value) => {
        violations.push(value);
      });
      await context.addInitScript(() => {
        document.addEventListener("securitypolicyviolation", (event) => {
          const record = (
            window as unknown as {
              recordPolicyViolation: (value: {
                directive: string;
                disposition: string;
              }) => Promise<void>;
            }
          ).recordPolicyViolation;
          void record({
            directive: event.effectiveDirective,
            disposition: event.disposition,
          });
        });
      });
      await use(violations);
      if (!allowCspViolations) expect(violations).toEqual([]);
    },
    { auto: true },
  ],
});
export { expect };
