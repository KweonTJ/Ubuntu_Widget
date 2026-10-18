"use strict";
const si = require("systeminformation");
const os = require("node:os");
const fs = require("node:fs");
const path = require("node:path");
const { execFile } = require("node:child_process");
const { promisify } = require("node:util");
const exec = promisify(execFile);
const validURL = (value) => {
  try {
    const u = new URL(value);
    return (
      ["http:", "https:"].includes(u.protocol) && !u.username && !u.password
    );
  } catch {
    return false;
  }
};
async function json(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    signal: AbortSignal.timeout(12000),
  });
  if (!response.ok) throw Error(`서버 응답 ${response.status}`);
  const text = await response.text();
  if (text.length > 2e6) throw Error("응답이 너무 큽니다");
  return JSON.parse(text);
}
class Providers {
  constructor(root) {
    this.root = root;
    this.data = {};
    this.weather = new Map();
    this.home = new Map();
    this.nativeAt = 0;
    this.nativeBusy = false;
    this.native = { media: { status: "empty" }, bluetooth: [] };
  }
  async windows(action = "Snapshot") {
    if (process.platform !== "win32")
      return {
        media: { status: "unavailable" },
        bluetooth: [],
        foreground: "",
      };
    const file = path.join(this.root, "native", "windows.ps1");
    const { stdout } = await exec(
      path.join(
        process.env.SystemRoot || "C:\\Windows",
        "System32",
        "WindowsPowerShell",
        "v1.0",
        "powershell.exe",
      ),
      [
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        file,
        "-Action",
        action,
      ],
      { windowsHide: true, timeout: 25000, maxBuffer: 4e6, encoding: "utf8" },
    );
    return JSON.parse(stdout.replace(/^\uFEFF/, "").trim());
  }
  async poll() {
    const calls = await Promise.allSettled([
      si.currentLoad(),
      si.mem(),
      si.fsSize(),
      si.networkStats(),
      si.battery(),
    ]);
    const v = (i) => (calls[i].status === "fulfilled" ? calls[i].value : null);
    const load = v(0),
      mem = v(1),
      disks = v(2),
      net = v(3),
      battery = v(4);
    const disk =
      disks?.find((d) =>
        process.platform === "win32"
          ? d.mount.toUpperCase() ===
            (process.env.SystemDrive || "C:").toUpperCase()
          : d.mount === "/",
      ) || disks?.[0];
    this.data = {
      cpu: load ? load.currentLoad : null,
      memory: mem
        ? {
            used: mem.active,
            total: mem.total,
            percent: (mem.active / mem.total) * 100,
          }
        : null,
      disk: disk
        ? { used: disk.used, total: disk.size, percent: disk.use }
        : null,
      network: net
        ? {
            down: net.reduce((s, n) => s + Math.max(0, n.rx_sec || 0), 0),
            up: net.reduce((s, n) => s + Math.max(0, n.tx_sec || 0), 0),
          }
        : null,
      battery: battery?.hasBattery
        ? { percent: battery.percent, charging: battery.isCharging }
        : null,
      uptime: os.uptime(),
      platform: process.platform,
    };
    if (!this.nativeBusy && Date.now() - this.nativeAt > 15000) {
      this.nativeBusy = true;
      this.windows()
        .then((v) => {
          this.native = v;
        })
        .catch(() => {
          this.native = {
            media: { status: "error" },
            bluetooth: [],
            error: "Windows 정보 읽기 실패",
          };
        })
        .finally(() => {
          this.nativeAt = Date.now();
          this.nativeBusy = false;
        });
    }
  }
  async weatherFor(c) {
    if (!Number.isFinite(c.latitude) || !Number.isFinite(c.longitude))
      return { status: "setup" };
    const key = `${c.latitude},${c.longitude}`;
    const old = this.weather.get(key);
    if (old && Date.now() - old.at < 600000) return old.value;
    try {
      const u = new URL("https://api.open-meteo.com/v1/forecast");
      u.search = new URLSearchParams({
        latitude: c.latitude,
        longitude: c.longitude,
        current: "temperature_2m,weather_code,is_day",
        daily: "temperature_2m_max,temperature_2m_min,weather_code",
        timezone: "auto",
      });
      const result = await json(u);
      const value = { status: "ready", ...result };
      this.weather.set(key, { at: Date.now(), value });
      return value;
    } catch {
      const value = { status: "error", message: "날씨 연결을 확인해 주세요" };
      this.weather.set(key, { at: Date.now() - 540000, value });
      return value;
    }
  }
  async cities(q) {
    if (typeof q !== "string" || q.trim().length < 2) return [];
    const u = new URL("https://geocoding-api.open-meteo.com/v1/search");
    u.search = new URLSearchParams({
      name: q.trim().slice(0, 100),
      count: 8,
      language: "ko",
      format: "json",
    });
    return (await json(u)).results || [];
  }
  async homeFor(c, token) {
    if (!validURL(c.server) || !token) return { status: "setup" };
    const key = c.server + "|" + c.entities;
    const old = this.home.get(key);
    if (old && Date.now() - old.at < 15000) return old.value;
    try {
      const states = await json(
        new URL("api/states", c.server.replace(/\/?$/, "/")),
        { headers: { Authorization: "Bearer " + token } },
      );
      const wanted = (c.entities || "")
        .split(",")
        .map((v) => v.trim())
        .filter(Boolean);
      const value = {
        status: "ready",
        entities: states
          .filter((e) => wanted.includes(e.entity_id))
          .map((e) => ({
            id: e.entity_id,
            name: e.attributes.friendly_name || e.entity_id,
            state: e.state,
            control: /^(light|switch)\./.test(e.entity_id),
          })),
      };
      this.home.set(key, { at: Date.now(), value });
      return value;
    } catch {
      return {
        status: "error",
        message: "서버 주소·토큰·인증서를 확인해 주세요",
      };
    }
  }
  async homeToggle(c, token, id) {
    if (
      !(c.entities || "")
        .split(",")
        .map((s) => s.trim())
        .includes(id) ||
      !/^(light|switch)\.[a-z0-9_]+$/.test(id) ||
      !validURL(c.server) ||
      !token
    )
      throw Error("등록된 기기만 제어할 수 있습니다.");
    await json(
      new URL(
        "api/services/" + id.split(".")[0] + "/toggle",
        c.server.replace(/\/?$/, "/"),
      ),
      {
        method: "POST",
        headers: {
          Authorization: "Bearer " + token,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ entity_id: id }),
      },
    );
    this.home.clear();
  }
  note(c) {
    if (!c.notePath) return { status: "setup" };
    try {
      const stat = fs.statSync(c.notePath);
      if (stat.size > 1024 * 1024) throw Error();
      return {
        status: "ready",
        text: fs.readFileSync(c.notePath, "utf8").slice(0, 16000),
      };
    } catch {
      return { status: "error", text: "노트 파일을 읽을 수 없습니다." };
    }
  }
  kdePath() {
    for (const p of [
      path.join(
        process.env.ProgramFiles || "C:\\Program Files",
        "KDE Connect",
        "bin",
        "kdeconnect-cli.exe",
      ),
      path.join(
        process.env.ProgramFiles || "C:\\Program Files",
        "KDE Connect",
        "kdeconnect-cli.exe",
      ),
    ])
      if (fs.existsSync(p)) return p;
    return null;
  }
  async devices() {
    const exe = this.kdePath();
    if (!exe) return [];
    const { stdout } = await exec(exe, ["--list-available", "--id-only"], {
      windowsHide: true,
      timeout: 12000,
      maxBuffer: 64000,
    });
    return stdout
      .trim()
      .split(/\r?\n/)
      .filter((s) => /^[a-zA-Z0-9_-]{1,128}$/.test(s));
  }
  async send(device, files) {
    const exe = this.kdePath();
    if (!exe || !(await this.devices()).includes(device))
      throw Error("연결된 KDE Connect 기기를 선택해 주세요.");
    for (const file of files)
      await exec(exe, ["--device", device, "--share", file], {
        windowsHide: true,
        timeout: 30000,
      });
  }
}
module.exports = { Providers, validURL };
