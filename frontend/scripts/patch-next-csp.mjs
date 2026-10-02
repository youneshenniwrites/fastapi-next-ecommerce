import process from "node:process";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// Temporary VIN-126 App Router nonce transport workaround, not an upstream fix.
// https://github.com/vercel/next.js/discussions/95259 reports production stripping
// standard CSP request headers; that discussion is reporter evidence, not an
// official confirmation of our deployment's cause. Our proxy must overwrite or
// remove x-vindor-render-csp on EVERY route before this renderer can trust it.
// Before upgrading Next, verify a supported nonce transport works in production,
// retain the stripped-header regression, then remove this script and its
// postinstall/prebuild hooks together and reinstall clean locked dependencies.
// Covers stable React's CJS/ESM App Router source and the webpack/Turbopack
// development/production runtimes selected by app-page/module.compiled.js.
// Experimental React bundles are deliberately unsupported, not silently patched.
const original =
  "    const csp = headers['content-security-policy'] || headers['content-security-policy-report-only'];";
const replacement =
  "    const csp = headers['x-vindor-render-csp'] || headers['content-security-policy'] || headers['content-security-policy-report-only'];";
const devOriginal =
  'headers["content-security-policy"]||headers["content-security-policy-report-only"]';
const devReplacement = 'headers["x-vindor-render-csp"]||' + devOriginal;
const prodOriginal =
  'u["content-security-policy"]||u["content-security-policy-report-only"]';
const prodReplacement = 'u["x-vindor-render-csp"]||' + prodOriginal;
const files = [
  {
    path: "dist/server/app-render/app-render.js",
    hash: "03ad1f5daa243d67c3a1ce7d11a25db6ff7620431a993ed7d081ca61ac84d0d8",
    before: original,
    after: replacement,
  },
  {
    path: "dist/esm/server/app-render/app-render.js",
    hash: "dd453bbeb71b1dbbb3f774442d52c1184ae6ab6c4037f2eae8958d99d5fa3cf3",
    before: original,
    after: replacement,
  },
  {
    path: "dist/compiled/next-server/app-page.runtime.dev.js",
    hash: "900814f488707dff14dfc66f313f64264c26621bc17a788d9d9ac6cd12e59645",
    before: devOriginal,
    after: devReplacement,
  },
  {
    path: "dist/compiled/next-server/app-page-turbo.runtime.dev.js",
    hash: "c3a724c261bd3b1f5cf6cdf236d14d1d55be142d5d552052271af09ec3bede7d",
    before: devOriginal,
    after: devReplacement,
  },
  {
    path: "dist/compiled/next-server/app-page.runtime.prod.js",
    hash: "afc6dfed1d8a1ce821180121db58cd7eff0d350ff12c7f1d7a95490819f526ba",
    before: prodOriginal,
    after: prodReplacement,
  },
  {
    path: "dist/compiled/next-server/app-page-turbo.runtime.prod.js",
    hash: "51ebd20128d7ef089886b9c3237fa71e3fee2f00c3f87803ede4261948186a0b",
    before: prodOriginal,
    after: prodReplacement,
  },
];
const sha256 = (source) => createHash("sha256").update(source).digest("hex");

export function patchNextCsp(nextDirectory) {
  const { version } = JSON.parse(
    readFileSync(join(nextDirectory, "package.json")),
  );
  if (version !== "16.3.6") {
    throw new Error(
      `Review/remove the Next CSP nonce workaround before using Next ${version}`,
    );
  }
  // Validate ALL complete sources before writing any. Only exact originals
  // and exactly reversible patches are accepted, including after a repeat install.
  const updates = files.map((file) => {
    const path = join(nextDirectory, file.path);
    const source = readFileSync(path, "utf8");
    if (sha256(source) === file.hash) {
      if (source.split(file.before).length !== 2) {
        throw new Error(`Unexpected patch target: ${file.path}`);
      }
      return { path, source: source.replace(file.before, file.after) };
    }
    const restored = source.replace(file.after, file.before);
    if (
      sha256(restored) !== file.hash ||
      source !== restored.replace(file.before, file.after)
    ) {
      throw new Error(
        `Unexpected Next source hash: ${file.path}; refusing to patch`,
      );
    }
    return null;
  });
  for (const update of updates) {
    if (update) writeFileSync(update.path, update.source);
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const require = createRequire(import.meta.url);
  patchNextCsp(dirname(require.resolve("next/package.json")));
}
