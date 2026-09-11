import { z } from "zod";

export function accountSchema(mode: "login" | "register") {
  return z.object({
    email: z
      .string()
      .trim()
      .min(1, "Enter your email address.")
      .max(254, "Use an email address of 254 characters or fewer.")
      .email({
        pattern: z.regexes.html5Email,
        message: "Enter a valid email address.",
      }),
    password: z
      .string()
      .min(
        mode === "register" ? 8 : 1,
        mode === "register"
          ? "Use at least 8 characters."
          : "Enter your password.",
      )
      .max(
        mode === "register" ? 128 : 1024,
        mode === "register"
          ? "Use 128 characters or fewer."
          : "Use 1024 characters or fewer.",
      ),
  });
}
export type AccountValues = z.infer<ReturnType<typeof accountSchema>>;
