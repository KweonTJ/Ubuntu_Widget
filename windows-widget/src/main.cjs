"use strict";
const {
  app,
  BrowserWindow,
  ipcMain,
  screen,
  nativeTheme,
  Menu,
  Tray,
  shell,
  dialog,
  powerMonitor,
  Notification,
  safeStorage,
} = require("electron");
const path = require("node:path");
const fs = require("node:fs");
const os = require("node:os");
const model = require("./model.cjs");
const { Store } = require("./store.cjs");
const { catalog, find } = require("./catalog.cjs");
const { Providers, validURL } = require("./providers.cjs");
const { Secrets } = require("./secrets.cjs");
const { Todomate } = require("./todomate.cjs");
const root = path.resolve(__dirname, "..");
const smoke = process.argv.includes("--smoke");
app.setPath(
  "userData",
  smoke
    ? path.join(root, ".smoke-profile")
    : path.join(app.getPath("appData"), "windows-widget"),
);
app.setAppUserModelId("io.github.kweontj.windowswidget");
let store,
  secrets,
  providers,
  todo,
  gallery,
  tray,
  quitting = false,
  timer,
  polling = false,
  drag = null;
const windows = new Map();
const timers = new Map();
const notifications = new Set();
let lastUsage = Date.now();
const html = path.join(root, "renderer", "index.html");
const local = (wc) =>
  wc &&
  !wc.isDestroyed() &&
  wc.getURL().split("?")[0] === require("node:url").pathToFileURL(html).href;
const work = (b) =>
  screen.getDisplayMatching(b || screen.getPrimaryDisplay().workArea).workArea;
const group = (id) => store.state.groups.find((g) => g.id === id);
const card = (id) =>
  store.state.groups.flatMap((g) => g.cards).find((c) => c.id === id);
function guard(w) {
  w.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  w.webContents.on("will-navigate", (e) => e.preventDefault());
  w.webContents.session.setPermissionRequestHandler((_wc, _p, cb) => cb(false));
}
function decorate(w) {
  const dark = nativeTheme.shouldUseDarkColors;
  if (process.platform === "win32") {
    try {
      w.setBackgroundMaterial(store.state.settings.glass ? "acrylic" : "none");
    } catch {}
  }
  w.setBackgroundColor(
    store.state.settings.glass ? "#00000000" : dark ? "#202227" : "#f4f3f1",
  );
}
function makeWidget(g) {
  if (windows.has(g.id)) return;
  g.bounds = model.bounds(g.bounds, work(g.bounds));
  const w = new BrowserWindow({
    ...g.bounds,
    show: false,
    frame: false,
    resizable: false,
    transparent: false,
    roundedCorners: true,
    skipTaskbar: true,
    alwaysOnTop: false,
    title: find(g.cards[g.active].kind).name,
    icon: path.join(root, "assets/icon.png"),
    backgroundColor: "#202227",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      sandbox: true,
      nodeIntegration: false,
      backgroundThrottling: false,
    },
  });
  windows.set(g.id, w);
  guard(w);
  decorate(w);
  w.setMenu(null);
  w.loadFile(html, { query: { group: g.id } });
  w.once("ready-to-show", () => {
    if (!smoke) w.showInactive();
  });
  w.on("close", (e) => {
    if (!quitting) {
      e.preventDefault();
      removeGroup(g.id);
    }
  });
  w.on("closed", () => windows.delete(g.id));
}
function library(selected) {
  if (!gallery || gallery.isDestroyed()) {
    gallery = new BrowserWindow({
      width: 1160,
      height: 790,
      minWidth: 840,
      minHeight: 600,
      show: false,
      title: "Widget Library",
      autoHideMenuBar: true,
      backgroundColor: "#17191d",
      icon: path.join(root, "assets/icon.png"),
      webPreferences: {
        preload: path.join(__dirname, "preload.cjs"),
        contextIsolation: true,
        sandbox: true,
        nodeIntegration: false,
      },
    });
    guard(gallery);
    gallery.loadFile(html);
    gallery.on("close", (e) => {
      if (!quitting) {
        e.preventDefault();
        gallery.hide();
      }
    });
    gallery.once("ready-to-show", () => {
      if (!smoke) gallery.show();
    });
  } else if (!smoke) {
    gallery.show();
    gallery.focus();
  }
  if (selected) {
    const send = () =>
      gallery.webContents.send("snapshot", { select: selected });
    if (gallery.webContents.isLoading())
      gallery.webContents.once("did-finish-load", send);
    else send();
  }
  return gallery;
}
function save() {
  store.save();
  broadcast();
}
function removeGroup(id) {
  const w = windows.get(id);
  windows.delete(id);
  w?.destroy();
  store.state.groups = store.state.groups.filter((g) => g.id !== id);
  save();
}
async function snapshot() {
  const cards = {};
  await Promise.all(
    store.state.groups
      .flatMap((g) => g.cards)
      .map(async (c) => {
        if (c.kind === "weather")
          cards[c.id] = await providers.weatherFor(c.config);
        if (c.kind === "note") cards[c.id] = providers.note(c.config);
        if (c.kind === "home")
          cards[c.id] = await providers.homeFor(c.config, secrets.get(c.id));
        if (c.kind === "focus")
          cards[c.id] = timers.get(c.id) || {
            remaining: (c.config.minutes || 25) * 60,
            running: false,
          };
      }),
  );
  return {
    state: store.state,
    catalog,
    data: { ...providers.data, ...providers.native, todo: todo.state, cards },
    theme: nativeTheme.shouldUseDarkColors ? "dark" : "light",
  };
}
async function broadcast() {
  const value = await snapshot();
  for (const w of [...windows.values(), gallery])
    if (w && !w.isDestroyed() && !w.webContents.isLoading())
      w.webContents.send("snapshot", value);
}
function sync() {
  for (const [id, w] of windows)
    if (!group(id)) {
      windows.delete(id);
      w.destroy();
    }
  for (const g of store.state.groups) {
    if (!windows.has(g.id)) makeWidget(g);
    const w = windows.get(g.id);
    const b = model.bounds(g.bounds, work(g.bounds));
    g.bounds = b;
    w.setBounds(b);
    decorate(w);
  }
  save();
}
function stopDrag() {
  if (!drag) return;
  clearInterval(drag.timer);
  const d = drag;
  drag = null;
  for (const w of windows.values()) w.webContents.send("snapshot", { target: false });
  const g = group(d.id);
  if (!g) return;
  if (d.changed && d.mode === "move") {
    const target = store.state.groups.find(
      (t) =>
        t !== g &&
        t.bounds.width === g.bounds.width &&
        t.bounds.height === g.bounds.height &&
        model.overlap(g.bounds, t.bounds) >= 0.65,
    );
    if (target) model.merge(store.state, g, target);
  }
  sync();
}
function startDrag(id, mode) {
  if (
    drag ||
    ![
      "move",
      "left",
      "right",
      "bottom",
      "left-bottom",
      "right-bottom",
    ].includes(mode)
  )
    return;
  const g = group(id);
  if (!g) return;
  const start = screen.getCursorScreenPoint(),
    b = { ...g.bounds };
  drag = { id, mode, b, start, changed: false, started: Date.now() };
  drag.timer = setInterval(() => {
    if (!drag) return;
    if (Date.now() - drag.started > 60000) {
      stopDrag();
      return;
    }
    const point = screen.getCursorScreenPoint(),
      dx = point.x - start.x,
      dy = point.y - start.y;
    if (Math.abs(dx) + Math.abs(dy) < 5 && !drag.changed) return;
    drag.changed = true;
    g.bounds = model.gesture(
      b,
      mode,
      dx,
      dy,
      work({ x: point.x, y: point.y, width: 1, height: 1 }),
    );
    windows.get(id)?.setBounds(g.bounds);
    for (const [other, w] of windows) {
      if (other === id) continue;
      const t = group(other);
      w.webContents.send("snapshot", {
        target: !!(
          t &&
          mode === "move" &&
          t.bounds.width === g.bounds.width &&
          t.bounds.height === g.bounds.height &&
          model.overlap(g.bounds, t.bounds) >= 0.65
        ),
      });
    }
  }, 16);
}
function context(id) {
  const g = group(id);
  if (!g) return;
  Menu.buildFromTemplate([
    { label: "위젯 보관함", click: () => library(g.cards[g.active].id) },
    {
      label: "크기",
      submenu: Object.entries(model.PRESETS).map(
        ([label, [width, height]]) => ({
          label: { small: "작게", medium: "중간", large: "크게" }[label],
          click: () => {
            g.bounds = model.bounds(
              { ...g.bounds, width, height },
              work(g.bounds),
            );
            sync();
          },
        }),
      ),
    },
    {
      label: "스택 해제",
      enabled: g.cards.length > 1,
      click: () => {
        model.split(store.state, g, work(g.bounds));
        sync();
      },
    },
    { type: "separator" },
    {
      label: "현재 위젯 삭제",
      click: () => {
        g.cards.splice(g.active, 1);
        if (!g.cards.length) removeGroup(id);
        else {
          g.active = Math.min(g.active, g.cards.length - 1);
          save();
        }
      },
    },
    {
      label: "스택 전체 삭제",
      enabled: g.cards.length > 1,
      click: () => removeGroup(id),
    },
  ]).popup({ window: windows.get(id) });
}
async function openURL(url) {
  if (!validURL(url)) throw Error("http 또는 https 주소를 입력해 주세요.");
  await shell.openExternal(url);
}
function applyTheme() {
  nativeTheme.themeSource = store.state.settings.theme;
  for (const w of windows.values()) decorate(w);
  broadcast();
}
async function action(event, name, p = {}) {
  if (!local(event.sender)) throw Error("지원하지 않는 요청");
  const own = [...windows].find(
    ([_id, w]) => w.webContents === event.sender,
  )?.[0];
  if (name === "snapshot") return snapshot();
  if (name === "drag") {
    if (own) startDrag(own, p.mode);
    return;
  }
  if (name === "drop") {
    if (own && drag?.id === own) stopDrag();
    return;
  }
  if (name === "context") {
    if (own) context(own);
    return;
  }
  if (name === "cycle") {
    const g = group(own);
    if (g) {
      g.active =
        (g.active + (p.direction === -1 ? -1 : 1) + g.cards.length) %
        g.cards.length;
      save();
    }
    return;
  }
  if (name === "library") {
    library(p.card);
    return;
  }
  if (name === "add") {
    const area = screen.getPrimaryDisplay().workArea;
    const [width, height] = model.PRESETS[p.size] || model.PRESETS.small;
    const offset = (store.state.groups.length * 32) % 160;
    const g = model.add(
      store.state,
      p.kind,
      p.config,
      model.bounds(
        { x: area.x + 32 + offset, y: area.y + 32 + offset, width, height },
        area,
      ),
    );
    if (p.kind === "home" && typeof p.token === "string" && p.token) {
      try {
        secrets.set(g.cards[0].id, p.token);
      } catch (e) {
        store.state.groups = store.state.groups.filter((x) => x !== g);
        throw e;
      }
    }
    makeWidget(g);
    if (p.kind === "todo") todo.ensure(false);
    save();
    return g.id;
  }
  if (name === "remove") {
    if (p.card) {
      const g = store.state.groups.find((g) =>
        g.cards.some((c) => c.id === p.card),
      );
      if (g) {
        g.cards = g.cards.filter((c) => c.id !== p.card);
        g.active = Math.min(g.active, g.cards.length - 1);
        if (!g.cards.length) removeGroup(g.id);
        else save();
      }
    }
    return;
  }
  if (name === "update") {
    const c = card(p.id);
    if (!c) throw Error("위젯을 다시 선택해 주세요.");
    c.config = model.config(p.config);
    if (typeof p.token === "string" && p.token) secrets.set(c.id, p.token);
    providers.home.clear();
    save();
    return true;
  }
  if (name === "settings") {
    for (const k of ["glass", "autostart", "usage"])
      if (typeof p[k] === "boolean") store.state.settings[k] = p[k];
    if (["system", "dark", "light"].includes(p.theme))
      store.state.settings.theme = p.theme;
    if (process.platform === "win32" && typeof p.autostart === "boolean")
      app.setLoginItemSettings({ openAtLogin: p.autostart, name: "WindowsWidget" });
    applyTheme();
    save();
    return;
  }
  if (name === "pickNote") {
    const r = await dialog.showOpenDialog(gallery, {
      properties: ["openFile"],
      filters: [{ name: "Markdown", extensions: ["md", "markdown", "txt"] }],
    });
    return r.canceled ? "" : r.filePaths[0];
  }
  if (name === "cities") return providers.cities(p.query);
  if (name === "open") {
    const c = card(p.id);
    if (!c) return;
    const meta = find(c.kind);
    if (c.kind === "note") {
      if (c.config.notePath) {
        const uri =
          "obsidian://open?" + new URLSearchParams({ path: c.config.notePath });
        await shell.openExternal(uri);
      }
      return;
    }
    if (c.kind === "todo") {
      todo.ensure(true);
      return;
    }
    if (c.kind === "stocks") return openURL("https://www.tossinvest.com/");
    if (c.kind === "sound" && process.platform === "win32")
      return shell.openExternal("ms-settings:sound");
    return openURL(c.config.url || meta.url);
  }
  if (name === "todoLogin") {
    todo.ensure(true);
    return;
  }
  if (name === "todoDisconnect") {
    await todo.disconnect();
    return;
  }
  if (name === "todoToggle") {
    await todo.toggle(p);
    return;
  }
  if (name === "media") {
    if (!["PlayPause", "Next", "Previous"].includes(p.command))
      throw Error("재생 명령 오류");
    const result = await providers.windows(p.command);
    if (!result.ok) throw Error("재생 중인 앱이 이 명령을 지원하지 않습니다.");
    providers.nativeAt = 0;
    return;
  }
  if (name === "home") {
    const c = card(p.id);
    if (c?.kind === "home")
      await providers.homeToggle(c.config, secrets.get(c.id), p.entity);
    await broadcast();
    return;
  }
  if (name === "devices") return providers.devices();
  if (name === "send") {
    const r = await dialog.showOpenDialog({
      title: "KDE Connect · 보낼 파일",
      properties: ["openFile", "multiSelections"],
    });
    if (!r.canceled) await providers.send(p.device, r.filePaths);
    return;
  }
  if (name === "focus") {
    const c = card(p.id);
    if (c?.kind !== "focus") return;
    let t = timers.get(c.id) || {
      remaining: (c.config.minutes || 25) * 60,
      running: false,
    };
    if (p.command === "reset") {
      t = { remaining: (c.config.minutes || 25) * 60, running: false };
      notifications.delete(c.id);
    } else if (t.running) {
      t = {
        remaining: Math.max(0, Math.ceil((t.endsAt - Date.now()) / 1000)),
        running: false,
      };
    } else {
      if (t.remaining <= 0) t.remaining = (c.config.minutes || 25) * 60;
      t = { ...t, running: true, endsAt: Date.now() + t.remaining * 1000 };
    }
    timers.set(c.id, t);
    broadcast();
    return;
  }
  throw Error("지원하지 않는 동작");
}
async function tick() {
  if (polling) return;
  polling = true;
  try {
    await providers.poll();
    const now = Date.now();
    for (const [id, t] of timers) {
      if (t.running && t.endsAt <= now && !notifications.has(id)) {
        t.running = false;
        t.remaining = 0;
        notifications.add(id);
        if (!smoke)
          new Notification({
            title: "집중 시간 완료",
            body: "잠시 쉬어 가세요.",
          }).show();
      }
    }
    if (
      store.state.settings.usage &&
      powerMonitor.getSystemIdleTime() < 60 &&
      providers.native.foreground
    ) {
      const date = new Date().toLocaleDateString("en-CA");
      if (store.state.usage.date !== date)
        store.state.usage = { date, apps: {} };
      const key = providers.native.foreground
        .replace(/[^\p{L}\p{N} ._()-]/gu, "")
        .slice(0, 80);
      if (!["__proto__", "constructor", "prototype"].includes(key))
        store.state.usage.apps[key] =
          (store.state.usage.apps[key] || 0) +
          Math.min((now - lastUsage) / 1000, 10);
      store.save();
    }
    lastUsage = now;
    await broadcast();
  } finally {
    polling = false;
  }
}
async function runSmoke() {
  setTimeout(() => {
    console.error("SMOKE timeout");
    app.exit(1);
  }, 30000).unref();
  console.log("SMOKE begin");
  const assert = require("node:assert/strict");
  const errors = [];
  gallery.webContents.on("console-message", (d) => {
    if (d.level === "error") errors.push(d.message);
  });
  if (gallery.webContents.isLoading())
    await new Promise((r) => gallery.webContents.once("did-finish-load", r));
  console.log("SMOKE gallery loaded");
  await new Promise((r) => setTimeout(r, 700));
  console.log("SMOKE gallery evaluate");
  assert(
    await gallery.webContents.executeJavaScript(
      '!!document.querySelector(".catalog-grid")',
    ),
  );
  console.log("SMOKE widget create");
  const g = model.add(
    store.state,
    "clock",
    {},
    model.bounds({ x: 32, y: 32, width: 320, height: 224 }, work()),
  );
  makeWidget(g);
  const w = windows.get(g.id);
  await new Promise((r) => w.webContents.once("did-finish-load", r));
  await broadcast();
  await new Promise((r) => setTimeout(r, 700));
  assert(
    await w.webContents.executeJavaScript(
      'document.body.textContent.includes("시계")',
    ),
  );
  console.log("SMOKE capture");
  fs.mkdirSync(path.join(root, "docs/images"), { recursive: true });
  fs.writeFileSync(
    path.join(root, "docs/images/windows-library.png"),
    (await gallery.webContents.capturePage()).toPNG(),
  );
  fs.writeFileSync(
    path.join(root, "docs/images/windows-clock.png"),
    (await w.webContents.capturePage()).toPNG(),
  );
  const other = model.add(store.state, "calendar", {}, g.bounds);
  makeWidget(other);
  assert(model.merge(store.state, other, g));
  sync();
  g.active = 1;
  await broadcast();
  assert.equal(g.cards.length, 2);
  model.split(store.state, g, work());
  sync();
  assert.equal(store.state.groups.length, 2);
  // Exercise the real IPC path and every renderer at minimum size in an isolated profile.
  await gallery.webContents.executeJavaScript(
    `window.widgets.invoke('add',{kind:'focus',size:'small',config:{minutes:15}})`,
  );
  const created = store.state.groups
    .flatMap((g) => g.cards)
    .find((c) => c.kind === "focus");
  assert(created);
  await gallery.webContents.executeJavaScript(
    `window.widgets.invoke('update',{id:${JSON.stringify(created.id)},config:{minutes:10}})`,
  );
  assert.equal(created.config.minutes, 10);
  await gallery.webContents.executeJavaScript(
    `window.widgets.invoke('remove',{card:${JSON.stringify(created.id)}})`,
  );
  assert(!card(created.id));
  const base = await snapshot();
  const sample = JSON.parse(JSON.stringify(base));
  sample.state.groups = [JSON.parse(JSON.stringify(g))];
  sample.state.groups[0].cards = sample.state.groups[0].cards.slice(0, 1);
  sample.state.groups[0].active = 0;
  sample.theme = "dark";
  sample.data.battery = { percent: 82, charging: false };
  sample.data.bluetooth = [{ name: "Test headphones", percent: 45 }];
  sample.data.cpu = 42;
  sample.data.memory = { used: 8e9, total: 16e9, percent: 50 };
  sample.data.disk = { used: 1e11, total: 5e11, percent: 20 };
  sample.data.media = {
    status: "ready",
    title: "Test track",
    artist: "Test artist",
    playing: true,
    art: "",
  };
  sample.data.todo = {
    status: "ready",
    date: "2026-10-18",
    tasks: [{ id: "sample", text: "Test task", done: false }],
    pending: [],
  };
  sample.state.settings.usage = true;
  sample.state.usage.apps = { "Test app": 4200 };
  for (const item of catalog) {
    const current = sample.state.groups[0].cards[0];
    current.kind = item.kind;
    current.config = {};
    sample.data.cards = {};
    w.setBounds({ ...g.bounds, width: 192, height: 96 });
    await w.webContents.executeJavaScript(`receive(${JSON.stringify(sample)})`);
    const text = await w.webContents.executeJavaScript(
      "document.body.textContent",
    );
    assert(!text.includes("NaN"), item.kind);
    assert(
      await w.webContents.executeJavaScript(
        '!!document.querySelector(".card .content")',
      ),
      item.kind,
    );
    if (["battery", "music", "screentime"].includes(item.kind)) {
      await w.webContents.executeJavaScript(
        `receive(${JSON.stringify(sample)});new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))`,
      );
      await new Promise((r) => setTimeout(r, 250));
      fs.writeFileSync(
        path.join(root, "docs/images/" + item.kind + "-minimum.png"),
        (await w.webContents.capturePage()).toPNG(),
      );
    }
  }
  nativeTheme.themeSource = "dark";
  await broadcast();
  await new Promise((r) => setTimeout(r, 250));
  fs.writeFileSync(
    path.join(root, "docs/images/windows-library-dark.png"),
    (await gallery.webContents.capturePage()).toPNG(),
  );
  assert.equal(errors.length, 0, errors.join("\n"));
  console.log(
    "SMOKE OK: gallery, 36 widget renders, IPC add/update/remove, stack, split, dark/light screenshots",
  );
  quitting = true;
  app.quit();
}
if (!smoke && !app.requestSingleInstanceLock()) app.quit();
else {
  app.on("second-instance", () => library());
  app.on("window-all-closed", () => {});
  app.on("before-quit", () => {
    quitting = true;
    clearInterval(timer);
    if (drag) clearInterval(drag.timer);
    todo?.close();
  });
  app
    .whenReady()
    .then(async () => {
      if (
        process.platform === "win32" &&
        Number(os.release().split(".")[2]) < 22000
      ) {
        await dialog.showMessageBox({
          type: "error",
          message: "Windows 11 이상이 필요합니다.",
        });
        app.quit();
        return;
      }
      store = new Store(app.getPath("userData"));
      if (smoke) {
        store.state = model.empty();
        store.state.settings.glass = false;
      }
      secrets = new Secrets(app.getPath("userData"), safeStorage);
      providers = new Providers(
        root.replace(/app\.asar$/, "app.asar.unpacked"),
      );
      todo = new Todomate(() => broadcast());
      ipcMain.handle("widgets", action);
      nativeTheme.themeSource = store.state.settings.theme;
      nativeTheme.on("updated", () => {
        for (const w of windows.values()) decorate(w);
        broadcast();
      });
      library();
      for (const g of store.state.groups) makeWidget(g);
      if (
        store.state.groups.some((g) => g.cards.some((c) => c.kind === "todo"))
      )
        todo.ensure();
      if (!smoke) {
        tray = new Tray(path.join(root, "assets/icon.png"));
        tray.setToolTip("Widget Library");
        tray.setContextMenu(
          Menu.buildFromTemplate([
            { label: "위젯 보관함", click: () => library() },
            {
              label: "모든 위젯 표시",
              click: () => {
                for (const w of windows.values()) {
                  w.showInactive();
                }
              },
            },
            { type: "separator" },
            { label: "종료", click: () => app.quit() },
          ]),
        );
        tray.on("click", () => library());
        timer = setInterval(() => tick().catch(() => {}), 3000);
        screen.on("display-metrics-changed", () => sync());
        screen.on("display-removed", () => sync());
        await tick();
      } else
        runSmoke().catch((e) => {
          console.error(e);
          quitting = true;
          app.exit(1);
        });
    })
    .catch((e) => {
      console.error(e);
      app.exit(1);
    });
}
