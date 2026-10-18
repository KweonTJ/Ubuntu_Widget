"use strict";
const test = require("node:test"),
  assert = require("node:assert/strict"),
  fs = require("node:fs"),
  vm = require("node:vm"),
  path = require("node:path");
const source = fs.readFileSync(
  path.join(__dirname, "../renderer/app.js"),
  "utf8",
);
function render(kind, data = {}, cfg = {}) {
  const fake = { addEventListener() {}, classList: { add() {}, toggle() {} } };
  const context = {
    window: {
      addEventListener() {},
      widgets: { invoke: () => new Promise(() => {}), subscribe() {} },
    },
    document: { querySelector: () => fake, body: fake, activeElement: null },
    location: { search: "" },
    URLSearchParams,
    console,
    setInterval() {},
    setTimeout() {},
    clearTimeout() {},
    matchMedia: () => ({ matches: false }),
  };
  vm.createContext(context);
  vm.runInContext(source, context);
  context.fixture = { kind, config: cfg, id: "test" };
  context.payload = {
    state: { groups: [], usage: { apps: {} }, settings: { usage: true } },
    theme: "dark",
    catalog: require("../src/catalog.cjs").catalog,
    data: { cards: {}, ...data },
  };
  vm.runInContext("snapshot=payload", context);
  return vm.runInContext("renderContent(fixture)", context);
}
test("task text and note content are escaped; completed tasks folded beneath unfinished", () => {
  const html = render("todo", {
    todo: {
      status: "ready",
      tasks: [
        { id: "a", text: "<img src=x>", done: true },
        { id: "b", text: "Still to do", done: false },
      ],
      pending: [],
      date: "2026-10-18",
    },
  });
  assert(html.indexOf("Still to do") < html.indexOf("<details"));
  assert(html.includes("&lt;img src=x&gt;"));
  assert(!/<details[^>]* open/.test(html));
  assert(!html.includes("<img src=x>"));
});
test("album cover precedes title and only bounded image data is used", () => {
  const html = render("music", {
    media: {
      status: "ready",
      title: "<track>",
      artist: "artist",
      art: "javascript:bad",
    },
  });
  assert(html.indexOf('class="art') < html.indexOf('class="title'));
  assert(!html.includes("javascript:bad"));
  assert(html.includes("&lt;track&gt;"));
});
test("battery devices keep visible name and percentage at every size", () => {
  const html = render("battery", {
    battery: { percent: 82, charging: true },
    bluetooth: [{ name: "My headset", percent: 45 }],
  });
  assert(html.includes("82%"));
  assert(html.includes("45%"));
  assert(html.includes("My headset"));
  assert(html.includes("battery-bluetooth-dark.svg"));
});
test("calendar week begins Sunday; screen time remains text", () => {
  const html = render("calendar");
  assert(html.indexOf(">일<") < html.indexOf(">월<"));
  const usage = render("screentime");
  assert(usage.includes("0분"));
  assert(!usage.includes("NaN"));
});
test("private notes are text and missing providers show setup rather than sample data", () => {
  const html = render("note", {
    cards: { test: { status: "ready", text: "<script>evil</script>" } },
  });
  assert(!html.includes("<script>"));
  assert(html.includes("&lt;script&gt;"));
  assert(render("weather").includes("도시를 선택"));
  assert(render("home").includes("연결하세요"));
});
