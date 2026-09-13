import process from "node:process";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// Temporary backport of https://github.com/vercel/next.js/pull/98168.
// Keep the request socket (protocol/address); detach only the response socket.
const original = `        const mocked = CALL({
            url: href,
            method,
            socket: _req.socket,
            maximumResponseBody
        });`;
const replacement = `        const mocked = {
            req: new REQUEST({
                url: href,
                method,
                headers: {},
                socket: _req.socket
            }),
            res: new RESPONSE({ maximumResponseBody })
        };`;
const files = [
  {
    path: "dist/server/image-optimizer.js",
    hash: "e9dae780db97eb11cbed0c5b1c872dc249fedfe9aab50132b43e5b54d34b47a8",
    call: "(0, _mockrequest.createRequestResponseMocks)",
    request: "_mockrequest.MockedRequest",
    response: "_mockrequest.MockedResponse",
  },
  {
    path: "dist/esm/server/image-optimizer.js",
    hash: "3ebd7bad4de250400b0f347cae2a17ab7ec03722914f3736260366df457e27d2",
    call: "createRequestResponseMocks",
    request: "MockedRequest",
    response: "MockedResponse",
  },
];
const oldImport =
  "import { createRequestResponseMocks } from './lib/mock-request';";
const newImport =
  "import { MockedRequest, MockedResponse } from './lib/mock-request';";
const sha256 = (source) => createHash("sha256").update(source).digest("hex");

export function patchNextImage(nextDirectory) {
  const { version } = JSON.parse(
    readFileSync(join(nextDirectory, "package.json")),
  );
  if (version !== "16.3.4") {
    throw new Error(
      `Review/remove the Next image backport before using Next ${version}`,
    );
  }
  // Validate both files before writing either; allow only exact original or
  // exactly reversible patched content, so repeat installs are idempotent.
  const updates = files.map((file) => {
    const path = join(nextDirectory, file.path);
    const source = readFileSync(path, "utf8");
    const before = original.replace("CALL", file.call);
    const after = replacement
      .replace("REQUEST", file.request)
      .replace("RESPONSE", file.response);
    const esm = file.path.includes("/esm/");
    if (sha256(source) === file.hash) {
      if (source.split(before).length !== 2)
        throw new Error(`Unexpected patch target: ${file.path}`);
      const patched = source.replace(before, after);
      return {
        path,
        source: esm ? patched.replace(oldImport, newImport) : patched,
      };
    }
    const reverted = source.replace(after, before);
    const restored = esm ? reverted.replace(newImport, oldImport) : reverted;
    const completePatch = restored.replace(before, after);
    const expected = esm
      ? completePatch.replace(oldImport, newImport)
      : completePatch;
    if (sha256(restored) !== file.hash || source !== expected) {
      throw new Error(
        `Unexpected Next source hash: ${file.path}; refusing to patch`,
      );
    }
    return null;
  });
  for (const update of updates)
    if (update) writeFileSync(update.path, update.source);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const require = createRequire(import.meta.url);
  patchNextImage(dirname(require.resolve("next/package.json")));
}
