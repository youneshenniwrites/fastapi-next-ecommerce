import assert from "node:assert/strict";
import {
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import process from "node:process";
import { test } from "node:test";
import { runInNewContext } from "node:vm";
import { patchNextCsp } from "./patch-next-csp.mjs";

const require = createRequire(import.meta.url);
const nextDirectory = dirname(require.resolve("next/package.json"));
const paths = [
  "dist/server/app-render/app-render.js",
  "dist/esm/server/app-render/app-render.js",
  "dist/compiled/next-server/app-page.runtime.dev.js",
  "dist/compiled/next-server/app-page-turbo.runtime.dev.js",
  "dist/compiled/next-server/app-page.runtime.prod.js",
  "dist/compiled/next-server/app-page-turbo.runtime.prod.js",
];
const original =
  "    const csp = headers['content-security-policy'] || headers['content-security-policy-report-only'];";
const patched =
  "    const csp = headers['x-vindor-render-csp'] || headers['content-security-policy'] || headers['content-security-policy-report-only'];";
const selections = paths.map((path) => {
  if (!path.includes("/compiled/")) return { before: original, after: patched };
  const headers = path.endsWith(".prod.js") ? "u" : "headers";
  const before = `${headers}["content-security-policy"]||${headers}["content-security-policy-report-only"]`;
  return { before, after: `${headers}["x-vindor-render-csp"]||${before}` };
});
// npm's postinstall may already have patched the installed package. Restore only
// the known one-line edit in test fixtures; the patch's full hashes still validate
// that these are the actual installed 16.3.8 sources, never handcrafted renderers.
const sources = paths.map((path, index) =>
  readFileSync(join(nextDirectory, path), "utf8").replace(
    selections[index].after,
    selections[index].before,
  ),
);

function fixture() {
  const directory = mkdtempSync(join(tmpdir(), "next-csp-patch-"));
  writeFileSync(
    join(directory, "package.json"),
    readFileSync(join(nextDirectory, "package.json")),
  );
  for (const [index, path] of paths.entries()) {
    mkdirSync(dirname(join(directory, path)), { recursive: true });
    writeFileSync(join(directory, path), sources[index]);
  }
  return directory;
}

function readSources(directory) {
  return paths.map((path) => readFileSync(join(directory, path), "utf8"));
}

function installedParser(source) {
  // parseRequestHeaders is internal to app-render, not exported. Execute its
  // installed function body with its REAL Next dependencies instead of copying
  // its implementation or importing the entire renderer outside Next's bundler.
  const match = source.match(
    /function parseRequestHeaders\(headers, options\) \{[\s\S]*?\n\}/,
  );
  assert.ok(match, "installed renderer contains parseRequestHeaders");
  const headers = require("next/dist/client/components/app-router-headers");
  const rsc = require("next/dist/server/lib/is-rsc-request");
  const router = require("next/dist/server/app-render/parse-and-validate-flight-router-state");
  const nonce = require("next/dist/server/app-render/get-script-nonce-from-header");
  const server = require("next/dist/server/server-utils");
  return runInNewContext(`(${match[0]})`, {
    process,
    ...headers,
    ...rsc,
    ...router,
    ...nonce,
    ...server,
    _approuterheaders: headers,
    _isrscrequest: rsc,
    _parseandvalidateflightrouterstate: router,
    _getscriptnoncefromheader: nonce,
    _serverutils: server,
  });
}

function compiledParser(source) {
  // Execute the exact nonce expression shipped in each selected stable runtime,
  // including its bundled nonce parser and regex; this is not a copied helper.
  const match = source.match(
    /nonce[=:]("string"==typeof\((?:csp|w)=[^?]+\)\?function[\s\S]*?\}\}\((?:csp|w)\):void 0)/,
  );
  assert.ok(match, "compiled App Router contains its CSP nonce extraction");
  const regexName = match[1].match(/\.match\((\w+)\)/)?.[1];
  assert.ok(regexName, "compiled nonce parser references its bundled regex");
  const declarationStart = source.indexOf(`let ${regexName}=`);
  assert.notEqual(declarationStart, -1);
  const declarationEnd = source.indexOf(";", declarationStart);
  const declaration = source.slice(declarationStart, declarationEnd + 1);
  return runInNewContext(
    `(headers => { let csp, w; const u = headers; ${declaration} return {nonce: ${match[1]}}; })`,
  );
}

const options = { isRoutePPREnabled: false, previewModeId: "test-preview" };
const policy = (nonce) => `default-src 'none'; script-src 'nonce-${nonce}'`;

test("the installed stable App Router selector uses guarded runtime files", () => {
  const selector = readFileSync(
    join(
      nextDirectory,
      "dist/server/route-modules/app-page/module.compiled.js",
    ),
    "utf8",
  );
  for (const NODE_ENV of ["development", "production"]) {
    for (const TURBOPACK of [undefined, "1"]) {
      const selected = { exports: undefined };
      runInNewContext(selector, {
        process: { env: { NODE_ENV, TURBOPACK } },
        module: selected,
        require: (path) => path,
      });
      assert.ok(paths.includes(selected.exports.replace(/^next\//, "")));
    }
  }
});

for (const [index, path] of paths.entries()) {
  const parse = path.includes("/compiled/") ? compiledParser : installedParser;
  test(`${path}: custom transport restores the stripped-header nonce`, () => {
    const directory = fixture();
    try {
      const stock = parse(sources[index]);
      const headers = { "x-vindor-render-csp": policy("fresh-request-nonce") };
      assert.equal(stock(headers, options).nonce, undefined);
      patchNextCsp(directory);
      const parser = parse(readSources(directory)[index]);
      assert.equal(parser(headers, options).nonce, "fresh-request-nonce");
      assert.equal(
        parser({ "x-vindor-render-csp": policy("another-nonce") }, options)
          .nonce,
        "another-nonce",
      );
      // The change affects only CSP selection, preserving the rest of parsing.
      assert.deepEqual(
        JSON.parse(JSON.stringify(parser(headers, options))),
        JSON.parse(
          JSON.stringify(
            stock(
              { "content-security-policy": policy("fresh-request-nonce") },
              options,
            ),
          ),
        ),
      );
    } finally {
      rmSync(directory, { recursive: true, force: true });
    }
  });

  test(`${path}: standard header fallback and existing validation are preserved`, () => {
    const directory = fixture();
    try {
      patchNextCsp(directory);
      const parser = parse(readSources(directory)[index]);
      for (const [headers, expected] of [
        [{ "content-security-policy": policy("enforced") }, "enforced"],
        [
          {
            "x-vindor-render-csp": policy("transport"),
            "content-security-policy": "frame-ancestors 'none'",
            "content-security-policy-report-only": policy("candidate"),
          },
          "transport",
        ],
        [
          { "content-security-policy-report-only": policy("candidate") },
          "candidate",
        ],
        [
          {
            "content-security-policy": policy("enforced"),
            "content-security-policy-report-only": policy("candidate"),
          },
          "enforced",
        ],
        [
          {
            "x-vindor-render-csp": policy("transport"),
            "content-security-policy": policy("enforced"),
            "content-security-policy-report-only": policy("candidate"),
          },
          "transport",
        ],
        [
          {
            "x-vindor-render-csp": "",
            "content-security-policy": policy("fallback"),
          },
          "fallback",
        ],
        [
          { "x-vindor-render-csp": "default-src 'nonce-default-source'" },
          "default-source",
        ],
        [{}, undefined],
        [{ "x-vindor-render-csp": "frame-ancestors 'none'" }, undefined],
        [{ "x-vindor-render-csp": policy("bad<script>") }, undefined],
        [{ "x-vindor-render-csp": policy("bad nonce") }, undefined],
        [{ "x-vindor-render-csp": policy("") }, undefined],
        [{ "x-vindor-render-csp": [policy("repeated-header")] }, undefined],
        [
          {
            "x-vindor-render-csp":
              "script-src 'nonce-invalid<> 'nonce-valid+/='",
          },
          "valid+/=",
        ],
      ]) {
        assert.equal(parser(headers, options).nonce, expected);
      }
    } finally {
      rmSync(directory, { recursive: true, force: true });
    }
  });
}

test("all sources patch exactly once and accept reversible mixed install states", () => {
  const directory = fixture();
  try {
    patchNextCsp(directory);
    const expected = sources.map((source, index) =>
      source.replace(selections[index].before, selections[index].after),
    );
    assert.deepEqual(readSources(directory), expected);
    patchNextCsp(directory);
    assert.deepEqual(readSources(directory), expected);
    for (const [index, path] of paths.entries()) {
      writeFileSync(join(directory, path), sources[index]);
      patchNextCsp(directory);
      assert.deepEqual(readSources(directory), expected);
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("unexpected versions and source edits reject before any source changes", () => {
  const directory = fixture();
  try {
    for (const version of ["16.3.6", "16.3.7", "16.3.9", "16.3.8-canary.0"]) {
      writeFileSync(
        join(directory, "package.json"),
        JSON.stringify({ version }),
      );
      assert.throws(() => patchNextCsp(directory), /Review\/remove/);
      assert.deepEqual(readSources(directory), sources);
    }
    writeFileSync(
      join(directory, "package.json"),
      JSON.stringify({ version: "16.3.8" }),
    );
    for (const [badIndex, badPath] of paths.entries()) {
      const { before: originalSelection, after: patchedSelection } =
        selections[badIndex];
      for (const validPatched of [false, true]) {
        for (const malformed of [
          sources[badIndex] + "\n// unexpected edit\n",
          sources[badIndex].replace(
            originalSelection,
            patchedSelection.replace(/\|\|[\s\S]*/, ""),
          ),
          sources[badIndex].replace(originalSelection, patchedSelection) +
            "\n// modified after patch\n",
        ]) {
          for (const [index, path] of paths.entries()) {
            writeFileSync(
              join(directory, path),
              validPatched
                ? sources[index].replace(
                    selections[index].before,
                    selections[index].after,
                  )
                : sources[index],
            );
          }
          writeFileSync(join(directory, badPath), malformed);
          const before = readSources(directory);
          assert.throws(
            () => patchNextCsp(directory),
            /Unexpected Next source hash/,
          );
          assert.deepEqual(readSources(directory), before);
        }
      }
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
