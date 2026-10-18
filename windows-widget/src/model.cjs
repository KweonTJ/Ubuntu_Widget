"use strict";
const { randomUUID } = require("node:crypto");
const { find } = require("./catalog.cjs");
const MIN = { width: 192, height: 96 },
  PRESETS = { small: [208, 208], medium: [320, 224], large: [432, 352] };
const snap = (v) => Math.round(v / 16) * 16;
const clamp = (v, min, max) => Math.min(Math.max(v, min), Math.max(min, max));
function bounds(b, work) {
  const width = clamp(
    snap(Number(b.width) || 208),
    Math.min(MIN.width, work.width),
    work.width,
  );
  const height = clamp(
    snap(Number(b.height) || 208),
    Math.min(MIN.height, work.height),
    work.height,
  );
  return {
    x: clamp(
      snap(Number.isFinite(Number(b.x)) ? Number(b.x) : work.x),
      work.x,
      work.x + work.width - width,
    ),
    y: clamp(
      snap(Number.isFinite(Number(b.y)) ? Number(b.y) : work.y),
      work.y,
      work.y + work.height - height,
    ),
    width,
    height,
  };
}
function gesture(b, mode, dx, dy, work) {
  let next = { ...b };
  if (mode === "move") {
    next.x += dx;
    next.y += dy;
  }
  if (mode.includes("right"))
    next.width = clamp(
      snap(b.width + dx),
      MIN.width,
      work.x + work.width - b.x,
    );
  if (mode.includes("left")) {
    next.width = clamp(snap(b.width - dx), MIN.width, b.x + b.width - work.x);
    next.x = b.x + b.width - next.width;
  }
  if (mode.includes("bottom"))
    next.height = clamp(
      snap(b.height + dy),
      MIN.height,
      work.y + work.height - b.y,
    );
  return bounds(next, work);
}
function overlap(a, b) {
  return (
    (Math.max(0, Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x)) *
      Math.max(
        0,
        Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y),
      )) /
    (a.width * a.height)
  );
}
const empty = () => ({
  schema: 1,
  settings: { theme: "system", glass: true, autostart: false, usage: false },
  groups: [],
  usage: { date: "", apps: {} },
});
function config(input = {}) {
  const out = {};
  for (const key of [
    "name",
    "url",
    "date",
    "title",
    "city",
    "timezone",
    "notePath",
    "vault",
    "note",
    "server",
    "entities",
    "events",
    "device",
  ])
    if (typeof input[key] === "string") out[key] = input[key].slice(0, 10000);
  if (Number.isFinite(+input.minutes))
    out.minutes = clamp(+input.minutes, 1, 240);
  if (
    input.latitude !== "" &&
    input.latitude !== null &&
    Number.isFinite(+input.latitude) &&
    Math.abs(+input.latitude) <= 90
  )
    out.latitude = +input.latitude;
  if (
    input.longitude !== "" &&
    input.longitude !== null &&
    Number.isFinite(+input.longitude) &&
    Math.abs(+input.longitude) <= 180
  )
    out.longitude = +input.longitude;
  return out;
}
function restore(raw) {
  const s = empty();
  if (!raw || raw.schema !== 1) return s;
  if (["system", "dark", "light"].includes(raw.settings?.theme))
    s.settings.theme = raw.settings.theme;
  for (const k of ["glass", "autostart", "usage"])
    if (typeof raw.settings?.[k] === "boolean") s.settings[k] = raw.settings[k];
  const seen = new Set();
  for (const g of (Array.isArray(raw.groups) ? raw.groups : []).slice(0, 100)) {
    if (typeof g.id !== "string" || seen.has(g.id) || !Array.isArray(g.cards))
      continue;
    const cards = g.cards
      .filter(
        (c) => c && typeof c.id === "string" && !seen.has(c.id) && find(c.kind),
      )
      .map((c) => {
        seen.add(c.id);
        return {
          id: c.id,
          kind: c.kind,
          config: config(c.config),
          origin: c.origin,
        };
      });
    if (!cards.length) continue;
    seen.add(g.id);
    s.groups.push({
      id: g.id,
      cards,
      active: clamp(Math.floor(Number(g.active) || 0), 0, cards.length - 1),
      bounds: g.bounds || { x: 32, y: 32, width: 208, height: 208 },
    });
  }
  if (
    raw.usage?.date === new Date().toLocaleDateString("en-CA") &&
    raw.usage.apps &&
    typeof raw.usage.apps === "object"
  ) {
    s.usage = { date: raw.usage.date, apps: {} };
    for (const [k, v] of Object.entries(raw.usage.apps).slice(0, 1000))
      if (
        !["__proto__", "constructor", "prototype"].includes(k) &&
        Number.isFinite(v) &&
        v >= 0
      )
        s.usage.apps[k.slice(0, 80)] = Math.min(v, 86400);
  }
  return s;
}
function add(s, kind, cfg, b) {
  if (!find(kind)) throw Error("알 수 없는 위젯");
  const g = {
    id: randomUUID(),
    cards: [{ id: randomUUID(), kind, config: config(cfg) }],
    active: 0,
    bounds: b,
  };
  s.groups.push(g);
  return g;
}
function merge(s, source, target) {
  if (
    source === target ||
    source.bounds.width !== target.bounds.width ||
    source.bounds.height !== target.bounds.height ||
    overlap(source.bounds, target.bounds) < 0.65
  )
    return false;
  for (const c of source.cards) {
    c.origin ||= { ...source.bounds };
    target.cards.push(c);
  }
  s.groups = s.groups.filter((g) => g !== source);
  return true;
}
function split(s, g, work) {
  if (g.cards.length < 2) return;
  const cards = g.cards.slice(1);
  g.cards = g.cards.slice(0, 1);
  g.active = 0;
  for (const [i, c] of cards.entries()) {
    const b = bounds(
      c.origin || {
        ...g.bounds,
        x: g.bounds.x + 32 * (i + 1),
        y: g.bounds.y + 32 * (i + 1),
      },
      work,
    );
    delete c.origin;
    s.groups.push({ id: randomUUID(), cards: [c], active: 0, bounds: b });
  }
}
module.exports = {
  MIN,
  PRESETS,
  snap,
  clamp,
  bounds,
  gesture,
  overlap,
  empty,
  restore,
  config,
  add,
  merge,
  split,
};
