import { setTimeout, clearTimeout } from "node:timers";
import assert from "node:assert/strict";
import {
  cpSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { createRequire } from "node:module";
import { Socket } from "node:net";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { patchNextImage } from "./patch-next-image.mjs";
const require = createRequire(import.meta.url);
const nextDirectory = dirname(require.resolve("next/package.json"));
patchNextImage(nextDirectory);
const { fetchInternalImage } = require("next/dist/server/image-optimizer");
const { serveStatic } = require("next/dist/server/serve-static");
const photo = new URL("../public/photos/headphones.webp", import.meta.url);
for (const disconnected of [false, true]) {
  test(`local image settles with ${disconnected ? "disconnected" : "live"} caller`, async () => {
    const socket = new Socket();
    socket.encrypted = true;
    Object.defineProperty(socket, "remoteAddress", { value: "192.0.2.1" });
    if (disconnected) socket.destroy();
    let timer;
    try {
      const result = await Promise.race([
        fetchInternalImage(
          "/photos/headphones.webp",
          { method: "HEAD", socket },
          {},
          1000000,
          async (request, response) => {
            assert.equal(request.socket, socket);
            assert.equal(request.socket.encrypted, true);
            assert.equal(request.socket.remoteAddress, "192.0.2.1");
            assert.equal(request.method, "GET");
            assert.equal(response.socket, null);
            await serveStatic(request, response, photo.pathname);
          },
        ),
        new Promise((_, reject) => {
          timer = setTimeout(
            () =>
              reject(
                new Error(
                  "Internal image fetch hung after caller disconnected",
                ),
              ),
            2000,
          );
        }),
      ]);
      assert.deepEqual(result.buffer, readFileSync(photo));
    } finally {
      clearTimeout(timer);
      socket.destroy();
    }
  });
}
test("internal image still enforces maximum response body", async () => {
  await assert.rejects(
    fetchInternalImage(
      "/photos/headphones.webp",
      { method: "GET" },
      {},
      1,
      async (_request, response) => {
        response.end(readFileSync(photo));
      },
    ),
    (error) => error.statusCode === 413,
  );
});
test("patch is idempotent and rejects unexpected versions or source", () => {
  const fixture = mkdtempSync(join(tmpdir(), "next-image-patch-"));
  try {
    cpSync(join(nextDirectory, "package.json"), join(fixture, "package.json"));
    for (const relative of [
      "dist/server/image-optimizer.js",
      "dist/esm/server/image-optimizer.js",
    ]) {
      cpSync(join(nextDirectory, relative), join(fixture, relative), {
        recursive: true,
      });
    }
    patchNextImage(fixture);
    patchNextImage(fixture);
    const target = join(fixture, "dist/server/image-optimizer.js");
    const content = readFileSync(target, "utf8");
    writeFileSync(target, content + "\n// unexpected modification\n");
    assert.throws(() => patchNextImage(fixture), /Unexpected Next source hash/);
    assert.equal(
      readFileSync(target, "utf8"),
      content + "\n// unexpected modification\n",
    );
    writeFileSync(
      join(fixture, "package.json"),
      JSON.stringify({ version: "16.3.5" }),
    );
    assert.throws(() => patchNextImage(fixture), /Review\/remove/);
  } finally {
    rmSync(fixture, { recursive: true, force: true });
  }
});
