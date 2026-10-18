"use strict";
const fs = require("node:fs");
const path = require("node:path");
class Secrets {
  constructor(dir, safe) {
    this.file = path.join(dir, "credentials.json");
    this.safe = safe;
    try {
      this.values = JSON.parse(fs.readFileSync(this.file, "utf8"));
    } catch {
      this.values = {};
    }
  }
  get(id) {
    try {
      return this.safe.isEncryptionAvailable()
        ? this.safe.decryptString(Buffer.from(this.values[id] || "", "base64"))
        : "";
    } catch {
      return "";
    }
  }
  set(id, value) {
    if (!this.safe.isEncryptionAvailable())
      throw Error("Windows 자격 증명 암호화를 사용할 수 없습니다.");
    if (value)
      this.values[id] = this.safe.encryptString(value).toString("base64");
    else delete this.values[id];
    const tmp = this.file + ".tmp";
    fs.writeFileSync(tmp, JSON.stringify(this.values), { mode: 0o600 });
    fs.renameSync(tmp, this.file);
  }
}
module.exports = { Secrets };
