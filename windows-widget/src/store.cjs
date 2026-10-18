"use strict";
const fs = require("node:fs");
const path = require("node:path");
const { empty, restore } = require("./model.cjs");
class Store {
  constructor(dir) {
    this.dir = dir;
    fs.mkdirSync(dir, { recursive: true });
    this.file = path.join(dir, "layout.json");
    try {
      this.state = restore(JSON.parse(fs.readFileSync(this.file, "utf8")));
    } catch (e) {
      if (e.code !== "ENOENT") {
        fs.copyFileSync(this.file, this.file + ".corrupt-" + Date.now());
      }
      this.state = empty();
    }
  }
  save() {
    const tmp = this.file + ".tmp";
    fs.writeFileSync(tmp, JSON.stringify(this.state, null, 2), { mode: 0o600 });
    fs.renameSync(tmp, this.file);
  }
}
module.exports = { Store };
