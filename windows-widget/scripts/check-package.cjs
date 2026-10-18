"use strict";
const assert = require("node:assert/strict"),
  fs = require("node:fs"),
  path = require("node:path");
const asar = require("@electron/asar");
const root = path.resolve(__dirname, ".."),
  archive = path.join(root, "dist/win-unpacked/resources/app.asar");
const list = asar.listPackage(archive);
for (const file of list) {
  assert(
    !/\/(?:\.smoke-profile|\.cache|\.web-profile|\.git|test|docs)\//.test(file),
    file,
  );
  assert(
    !/\/(?:layout|credentials|connections|positions|widget-stacks)\.json$/.test(
      file,
    ),
    file,
  );
}
for (const dir of ["src", "renderer", "assets", "native"])
  for (const file of fs.readdirSync(path.join(root, dir))) {
    const local = path.join(root, dir, file);
    if (!fs.statSync(local).isFile()) continue;
    const packaged = asar.extractFile(archive, dir + "/" + file);
    assert.deepEqual(
      packaged,
      fs.readFileSync(local),
      "stale package: " + dir + "/" + file,
    );
  }
assert.equal(
  JSON.parse(asar.extractFile(archive, "package.json")).version,
  require("../package.json").version,
);
assert(list.includes("/node_modules/systeminformation/LICENSE"));
assert(
  fs.existsSync(path.join(root, "dist/win-unpacked/LICENSES.chromium.html")),
);
console.log(
  "PACKAGE OK: source match, clean defaults, production dependency and runtime licenses",
);
