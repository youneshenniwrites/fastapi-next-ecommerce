import { z } from "zod";

// Zod's optional JIT probes/compiles with Function(). Even a caught probe
// emits CSP reports. Keep the same schemas on its CSP-compatible interpreter.
z.config({ jitless: true });
export { z };
