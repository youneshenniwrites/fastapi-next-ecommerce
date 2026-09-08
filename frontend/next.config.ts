import type { NextConfig } from "next";
const config: NextConfig = {
  poweredByHeader: false,
  // Vercel's adapter packages functions; standalone output is for local containers.
  output: process.env.VERCEL === "1" ? undefined : "standalone",
};
export default config;
