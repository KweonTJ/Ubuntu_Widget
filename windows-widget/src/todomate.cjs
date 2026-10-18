"use strict";
const { BrowserWindow, session } = require("electron");
const fs = require("node:fs");
const path = require("node:path");
const allowed = (url) => {
  try {
    return (
      new URL(url).protocol === "https:" &&
      [
        "www.todomate.net",
        "todomate.net",
        "accounts.google.com",
        "appleid.apple.com",
      ].includes(new URL(url).hostname)
    );
  } catch {
    return false;
  }
};
class Todomate {
  constructor(changed) {
    this.changed = changed;
    this.state = { status: "signed_out", tasks: [], pending: [], date: "" };
    this.window = null;
  }
  ensure(show = false) {
    if (this.window && !this.window.isDestroyed()) {
      if (show) this.window.show();
      return this.window;
    }
    this.quitting = false;
    const profile = session.fromPartition("persist:todomate");
    profile.setPermissionRequestHandler((_wc, _p, callback) => callback(false));
    const win = (this.window = new BrowserWindow({
      width: 1050,
      height: 800,
      show,
      title: "todomate · 연결",
      autoHideMenuBar: true,
      webPreferences: {
        session: profile,
        nodeIntegration: false,
        contextIsolation: true,
        sandbox: true,
      },
    }));
    win.webContents.setWindowOpenHandler(({ url }) =>
      allowed(url)
        ? {
            action: "allow",
            overrideBrowserWindowOptions: {
              autoHideMenuBar: true,
              webPreferences: {
                session: profile,
                nodeIntegration: false,
                contextIsolation: true,
                sandbox: true,
              },
            },
          }
        : { action: "deny" },
    );
    win.webContents.on("will-navigate", (e, url) => {
      if (!allowed(url)) e.preventDefault();
    });
    win.webContents.on("console-message", (details) => {
      if (
        !details.message?.startsWith("UW_TODOMATE:") ||
        !["www.todomate.net", "todomate.net"].includes(
          new URL(win.webContents.getURL()).hostname,
        )
      )
        return;
      try {
        const v = JSON.parse(details.message.slice(12));
        this.state = {
          status: String(v.status),
          date: String(v.date),
          error: String(v.error || ""),
          pending: Array.isArray(v.pending)
            ? v.pending.filter((x) => typeof x === "string")
            : [],
          tasks: (Array.isArray(v.tasks) ? v.tasks : [])
            .slice(0, 500)
            .filter(
              (t) =>
                typeof t.id === "string" &&
                typeof t.text === "string" &&
                typeof t.done === "boolean",
            )
            .map((t) => ({
              id: t.id,
              text: t.text.slice(0, 1000),
              done: t.done,
            })),
        };
        this.changed();
      } catch {}
    });
    win.webContents.on("did-finish-load", () => {
      if (
        ["www.todomate.net", "todomate.net"].includes(
          new URL(win.webContents.getURL()).hostname,
        )
      )
        win.webContents
          .executeJavaScript(
            fs.readFileSync(path.join(__dirname, "todomate-page.js"), "utf8"),
          )
          .catch(() => {});
    });
    win.webContents.on("did-fail-load", () => {
      this.state.status = "error";
      this.changed();
    });
    win.on("close", (e) => {
      if (!this.quitting) {
        e.preventDefault();
        win.hide();
      }
    });
    win.loadURL("https://www.todomate.net/");
    return win;
  }
  async toggle({ id, done, date }) {
    if (
      !this.state.tasks.some((t) => t.id === id && t.done === done) ||
      date !== this.state.date
    )
      throw Error("목록이 변경되었습니다. 다시 시도해 주세요.");
    await this.ensure().webContents.executeJavaScript(
      `window.uwTodomate?.toggle(${JSON.stringify(id)},${JSON.stringify(done)},${JSON.stringify(date)})`,
    );
  }
  async disconnect() {
    this.quitting = true;
    if (this.window && !this.window.isDestroyed()) this.window.destroy();
    this.window = null;
    await session.fromPartition("persist:todomate").clearStorageData();
    this.state = { status: "signed_out", tasks: [], pending: [], date: "" };
    this.changed();
  }
  close() {
    this.quitting = true;
    if (this.window && !this.window.isDestroyed()) this.window.destroy();
  }
}
module.exports = { Todomate };
