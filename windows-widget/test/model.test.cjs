"use strict";
const test = require("node:test"),
  assert = require("node:assert/strict");
const m = require("../src/model.cjs");
const { Store } = require("../src/store.cjs");
const { validURL } = require("../src/providers.cjs");
const fs = require("node:fs"),
  os = require("node:os"),
  path = require("node:path");
const work = { x: 0, y: 0, width: 1920, height: 1040 };
test("off-screen and oversized cards are clamped to work area, including negative monitors", () => {
  assert.deepEqual(
    m.bounds({ x: 4000, y: 2000, width: 208, height: 208 }, work),
    { x: 1712, y: 832, width: 208, height: 208 },
  );
  const monitor = { x: -1920, y: 0, width: 1920, height: 1080 };
  const b = m.bounds({ x: -2000, y: -100, width: 3000, height: 2000 }, monitor);
  assert.deepEqual(b, { x: -1920, y: 0, width: 1920, height: 1080 });
});
test("left resize preserves opposite edge and bottom resize works for whole edge", () => {
  const b = { x: 320, y: 160, width: 320, height: 224 };
  const left = m.gesture(b, "left", -70, 0, work);
  assert.equal(left.x + left.width, b.x + b.width);
  assert.equal(left.width, 384);
  const bottom = m.gesture(b, "bottom", 100, -500, work);
  assert.equal(bottom.height, 96);
  assert.equal(bottom.x, b.x);
  assert.equal(bottom.width, b.width);
});
test("drag-to-stack requires same dimensions and 65 percent overlap", () => {
  const s = m.empty(),
    a = m.add(s, "clock", {}, { x: 0, y: 0, width: 208, height: 208 }),
    b = m.add(s, "calendar", {}, { x: 80, y: 0, width: 208, height: 208 });
  assert(!m.merge(s, a, b));
  b.bounds.x = 16;
  assert(m.merge(s, a, b));
  assert.equal(s.groups.length, 1);
  assert.equal(b.cards.length, 2);
  assert.equal(b.bounds.x, 16);
  b.active = 1;
  const before = { ...b.bounds };
  b.active = 0;
  assert.deepEqual(b.bounds, before);
  m.split(s, b, work);
  assert.equal(s.groups.length, 2);
  assert.equal(s.groups[1].bounds.x, 0);
  const c = m.add(s, "music", {}, { x: 16, y: 0, width: 320, height: 224 });
  assert(!m.merge(s, c, b));
});
test("merge two stacks preserves all members and split survives restart", () => {
  const s = m.empty(),
    box = { x: 32, y: 32, width: 208, height: 208 };
  const a = m.add(s, "clock", {}, box),
    b = m.add(s, "calendar", {}, box),
    c = m.add(s, "today", {}, box),
    d = m.add(s, "focus", {}, box);
  m.merge(s, b, a);
  m.merge(s, d, c);
  m.merge(s, c, a);
  const r = m.restore(JSON.parse(JSON.stringify(s)));
  assert.equal(r.groups[0].cards.length, 4);
  m.split(r, r.groups[0], work);
  assert.equal(r.groups.length, 4);
});
test("state and input configuration exclude tokens and unknown widget kinds", () => {
  const s = m.empty();
  m.add(
    s,
    "note",
    { token: "SECRET", notePath: "C:\\Notes\\hi.md", minutes: 999 },
    work,
  );
  const r = m.restore(JSON.parse(JSON.stringify(s)));
  assert(!JSON.stringify(r).includes("SECRET"));
  assert.equal(r.groups[0].cards[0].config.minutes, 240);
  assert.throws(() => m.add(s, "untrusted", {}, work));
  assert.equal(m.restore({ schema: 9 }).groups.length, 0);
});
test("atomic state save preserves layout, corrupt state is backed up", () => {
  const dir = fs.mkdtempSync(
    path.join(process.env.WIDGET_TEST_TEMP || os.tmpdir(), "widget-test-"),
  );
  try {
    const s = new Store(dir);
    m.add(s.state, "clock", {}, work);
    s.save();
    assert.equal(new Store(dir).state.groups.length, 1);
    fs.writeFileSync(s.file, "not json");
    assert.equal(new Store(dir).state.groups.length, 0);
    assert(fs.readdirSync(dir).some((f) => f.includes(".corrupt-")));
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
test("website links reject executable, file and credential URLs", () => {
  for (const u of [
    "javascript:alert(1)",
    "file:///C:/Users/",
    "https://name:secret@example.com/",
    "ms-settings:camera",
    "not a URL",
  ])
    assert(!validURL(u));
  assert(validURL("https://example.com/a?q=b"));
  assert(validURL("http://home.local:8123/"));
});
test("blank weather coordinates do not silently select the Gulf of Guinea", () => {
  const c = m.config({ city: "", latitude: "", longitude: "" });
  assert.equal(c.latitude, undefined);
  assert.equal(c.longitude, undefined);
  assert.deepEqual(m.config({ latitude: "0", longitude: "0" }), {
    latitude: 0,
    longitude: 0,
  });
});
test("fractional saved page indices and invalid usage cannot break restoration", () => {
  const s = m.empty();
  const g = m.add(s, "clock", {}, work);
  g.active = 1.5;
  const r = m.restore(s);
  assert.equal(r.groups[0].active, 0);
  assert(Number.isInteger(r.groups[0].active));
});
