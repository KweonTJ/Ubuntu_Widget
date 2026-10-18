"use strict";
const api = window.widgets,
  app = document.querySelector("#app");
const groupId = new URLSearchParams(location.search).get("group");
let lastMarkup = "";
let snapshot,
  category = "전체",
  query = "",
  selected = "clock",
  editing = null,
  size = "small",
  lastActive = "",
  completedOpen = false,
  cities = [],
  target = false,
  searchTimer;
const esc = (v) =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const num = (v, d = 0) => (Number.isFinite(Number(v)) ? Number(v) : d);
const pct = (v) => Math.max(0, Math.min(100, num(v)));
const bytes = (v) => {
  v = num(v);
  return v >= 1e9
    ? (v / 1e9).toFixed(1) + " GB"
    : v >= 1e6
      ? (v / 1e6).toFixed(1) + " MB"
      : v >= 1e3
        ? (v / 1e3).toFixed(0) + " KB"
        : Math.round(v) + " B";
};
const meta = (kind) => snapshot.catalog.find((c) => c.kind === kind);
// All built-in icons are local; no remote content is rendered with HTML privileges.
const image = (name) =>
  `../assets/${name}${snapshot?.theme === "dark" ? "-dark" : ""}.svg`;
function toast(message) {
  const t = document.querySelector("#toast");
  t.textContent = message;
  t.classList.add("visible");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => t.classList.remove("visible"), 4500);
}
async function call(name, p = {}) {
  try {
    return await api.invoke(name, p);
  } catch (e) {
    toast(
      e.message.replace(/^Error invoking remote method '[^']+': Error: /, ""),
    );
    return undefined;
  }
}
const allCards = () =>
  snapshot.state.groups.flatMap((g) =>
    g.cards.map((c) => ({ ...c, group: g })),
  );
function field(name, label, value = "", type = "text") {
  return `<label>${esc(label)}<input type="${type}" name="${name}" value="${esc(value)}" ${type === "password" ? 'autocomplete="new-password"' : ""}></label>`;
}
function textarea(name, label, value = "") {
  return `<label>${esc(label)}<textarea name="${name}">${esc(value)}</textarea></label>`;
}
function settingsForm(kind, c = {}) {
  let out = "";
  if (kind === "website")
    out +=
      field("name", "위젯 이름", c.name) +
      field("url", "웹사이트 주소", c.url, "url");
  if (kind === "weather")
    out +=
      field("city", "도시 검색 (영문 이름도 지원)", c.city) +
      `<button type="button" data-action="cities">도시 찾기</button><div class="city-results">${cities.map((v, i) => `<button type="button" data-action="chooseCity" data-index="${i}">${esc(v.name)} · ${esc(v.admin1 || v.country || "")}</button>`).join("")}</div>` +
      field("latitude", "위도", c.latitude ?? "", "number") +
      field("longitude", "경도", c.longitude ?? "", "number");
  if (kind === "countdown")
    out +=
      field("title", "제목", c.title) + field("date", "날짜", c.date, "date");
  if (kind === "focus")
    out += field("minutes", "집중 시간 (1–240분)", c.minutes || 25, "number");
  if (kind === "note")
    out +=
      field("notePath", "Markdown 파일", c.notePath) +
      `<button type="button" data-action="pickNote">파일 선택…</button><p class="help">읽기 전용으로 표시합니다. Obsidian이 설치되어 있고, 선택한 파일이 보관함 안에 있어야 Obsidian에서 열 수 있습니다.</p>`;
  if (kind === "agenda")
    out += textarea(
      "events",
      "한 줄에 날짜 시간 | 일정 (예: 2026-12-01 14:00 | 회의)",
      c.events,
    );
  if (kind === "home")
    out +=
      field("server", "Home Assistant 주소", c.server, "url") +
      field("entities", "기기 ID (쉼표 구분)", c.entities) +
      field("token", "장기 액세스 토큰 (변경할 때만 입력)", "", "password") +
      '<p class="help">토큰은 Windows 사용자 자격 증명으로 암호화해 별도 저장합니다. http는 신뢰하는 로컬 네트워크에서만 사용하세요.</p>';
  if (kind === "todo")
    out +=
      '<button type="button" data-action="todoLogin">todomate 로그인 / 열기</button><p class="help">공식 웹사이트에서 직접 로그인하세요. 오늘의 내 할 일만 읽고 체크합니다. 공식 API가 아닌 호환 연결로, 서비스 변경 시 작동하지 않을 수 있습니다.</p><button type="button" class="quiet" data-action="todoDisconnect">연결 해제 및 로그인 데이터 삭제</button>';
  if (kind === "kdeconnect")
    out +=
      '<p class="help">Windows용 KDE Connect를 설치하고 기기를 페어링하세요. 기본 설치 경로의 kdeconnect-cli.exe를 사용합니다. 파일은 선택 후에만 전송합니다.</p>';
  if (kind === "stocks")
    out +=
      '<p class="help">Windows 초판은 토스증권 바로가기입니다. 검증되지 않은 API나 계정 키를 수집하지 않습니다.</p>';
  if (kind === "screentime")
    out +=
      '<p class="help">전체 설정에서 사용 시간 기록을 켜세요. 앱이 실행 중이고 PC 입력이 60초 이상 멈추지 않았을 때만 기록합니다. 창 제목이나 웹 주소는 저장하지 않습니다.</p>';
  return out;
}
function inspector() {
  const c = editing ? allCards().find((c) => c.id === editing) : null;
  const m = meta(c?.kind || selected);
  if (!m) return "";
  return `<div class="preview"><div class="preview-widget widget"><article class="card"><header>${esc(c?.config.name || m.name)}</header><div class="content">${renderContent(c || { id: "preview", kind: m.kind, config: {} })}</div></article></div></div><h2>${esc(c?.config.name || m.name)}</h2><p class="subtitle">${esc(m.description)}</p><form id="config-form">${settingsForm(m.kind, c?.config || {})}${
    !c
      ? `<label>크기<select name="size">${[
          ["small", "작게 · 208 × 208"],
          ["medium", "중간 · 320 × 224"],
          ["large", "크게 · 432 × 352"],
        ]
          .map(
            ([v, label]) =>
              `<option value="${v}" ${size === v ? "selected" : ""}>${label}</option>`,
          )
          .join("")}</select></label>`
      : ""
  }<div class="actions"><button class="primary" type="submit">${c ? "변경 저장" : "바탕화면에 추가"}</button>${c ? '<button class="quiet danger" data-action="remove" type="button">위젯 삭제</button>' : ""}</div></form><p class="help">이동은 위젯 몸체를 드래그하세요.<br>양옆과 하단 전체에서 크기를 조절합니다.<br>같은 크기끼리 겹치면 스택이 됩니다.<br>오른쪽 클릭으로 삭제·크기·스택을 관리합니다.</p>`;
}
function renderGallery() {
  const categories = [
    "전체",
    "내 바탕화면",
    ...new Set(snapshot.catalog.map((m) => m.category)),
    "설정",
  ];
  let content = "";
  if (category === "설정")
    content = `<h1>설정</h1><p class="help">모든 위젯에 같은 설정이 적용됩니다.</p><div class="settings-row"><div>모양<p>Windows의 밝기 모드를 따를 수 있습니다.</p></div><select id="theme">${[
      ["system", "시스템"],
      ["light", "라이트"],
      ["dark", "다크"],
    ]
      .map(
        ([v, n]) =>
          `<option value="${v}" ${snapshot.state.settings.theme === v ? "selected" : ""}>${n}</option>`,
      )
      .join("")}</select></div>${[
      ["glass", "글래스 효과", "Windows 11 Acrylic 배경을 사용합니다."],
      ["autostart", "로그인 시 시작", "Windows 로그인 후 위젯을 복원합니다."],
      ["usage", "사용 시간 기록", "이 PC의 앱 이름과 사용 시간만 저장합니다."],
    ]
      .map(
        ([k, n, d]) =>
          `<div class="settings-row"><div>${n}<p>${d}</p></div><input type="checkbox" data-setting="${k}" aria-label="${n}" ${snapshot.state.settings[k] ? "checked" : ""}></div>`,
      )
      .join(
        "",
      )}<p class="help">Widget Library 1.0.0 · Windows 11<br>위젯과 연결 데이터는 Windows 사용자 프로필에 저장합니다.<br>창을 닫아도 트레이에서 실행됩니다. 종료는 트레이 메뉴를 이용하세요.</p>`;
  else if (category === "내 바탕화면") {
    const cards = allCards();
    content = `<header><div><h1>내 바탕화면</h1><p>${cards.length}개의 위젯</p></div></header>${cards.length ? cards.map((c) => `<div class="placed"><img src="${image(meta(c.kind).icon)}" alt=""><div class="info"><strong>${esc(c.config.name || meta(c.kind).name)}</strong><small>${c.group.bounds.width} × ${c.group.bounds.height}${c.group.cards.length > 1 ? " · 스택 " + c.group.cards.length + "개" : ""}</small></div><button data-action="edit" data-id="${c.id}">설정</button><button data-action="removeCard" data-id="${c.id}" class="quiet danger">삭제</button></div>`).join("") : '<p class="help">위젯을 골라 바탕화면을 꾸며 보세요.</p>'}`;
  } else {
    const items = snapshot.catalog.filter(
      (m) =>
        (category === "전체" || m.category === category) &&
        (!query ||
          `${m.name} ${m.description}`
            .toLowerCase()
            .includes(query.toLowerCase())),
    );
    content = `<header><div><h1>${esc(category === "전체" ? "위젯 보관함" : category)}</h1><p>필요한 정보만, 원하는 자리에.</p></div><input class="search" id="search" placeholder="위젯 검색" aria-label="위젯 검색" value="${esc(query)}"></header><div class="catalog-grid">${items.map((m) => `<button class="tile ${selected === m.kind && !editing ? "selected" : ""}" data-action="select" data-kind="${m.kind}"><img src="${image(m.icon)}" alt=""><h3>${esc(m.name)}</h3><span>${esc(m.description)}</span></button>`).join("")}</div>`;
  }
  const scroll = document.querySelector(".library-main")?.scrollTop || 0;
  app.innerHTML = `<div class="shell"><nav class="sidebar"><div class="brand"><img src="../assets/icon.png" alt="">Widget Library</div>${categories.map((c) => `<button class="${category === c ? "active" : ""}" data-action="category" data-category="${esc(c)}">${esc(c)}</button>`).join("")}<footer>Windows 11<br>Desktop collection</footer></nav><main class="library-main">${content}</main><aside class="inspector">${inspector()}</aside></div>`;
  document.querySelector(".library-main").scrollTop = scroll;
}
const center = (big, small = "") =>
  `<div class="center"><div class="big">${big}</div>${small ? `<div class="caption">${small}</div>` : ""}</div>`;
const hint = (text) => `<p class="hint">${esc(text)}</p>`;
function bar(name, value, caption) {
  return `<div class="metric"><div class="metric-head"><span>${esc(name)}</span><span>${esc(caption || Math.round(pct(value)) + "%")}</span></div><div class="track"><i style="width:${pct(value)}%"></i></div></div>`;
}
const fullDate = (d) =>
  d.toLocaleDateString("ko-KR", {
    month: "long",
    day: "numeric",
    weekday: "long",
  });
function weatherName(code, day) {
  if (code === 0) return day ? "clear-day" : "clear-night";
  if (code <= 2) return day ? "partly-cloudy-day" : "partly-cloudy-night";
  if (code === 3) return "cloudy";
  if (code <= 48) return "fog";
  if (code <= 55) return "drizzle";
  if (code <= 57) return "freezing-rain";
  if (code <= 67) return "rain";
  if (code <= 77) return "snow";
  if (code <= 82) return day ? "showers-day" : "showers-night";
  if (code <= 86) return "snow";
  if (code >= 95) return "thunderstorm";
  return "unknown";
}
function renderContent(c) {
  const now = new Date(),
    cfg = c.config || {},
    data = snapshot.data,
    d = data.cards[c.id];
  switch (c.kind) {
    case "clock":
      return center(
        now.toLocaleTimeString("ko-KR", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        }),
        esc(fullDate(now)),
      );
    case "today":
      return center(
        now.getDate(),
        esc(
          now.toLocaleDateString("ko-KR", {
            year: "numeric",
            month: "long",
            weekday: "long",
          }),
        ),
      );
    case "calendar": {
      const y = now.getFullYear(),
        m = now.getMonth(),
        offset = new Date(y, m, 1).getDay(),
        count = new Date(y, m + 1, 0).getDate();
      return `<div class="month">${y}년 ${m + 1}월</div><div class="calendar">${["일", "월", "화", "수", "목", "금", "토"].map((s, i) => `<span class="${i === 0 ? "sun" : ""}">${s}</span>`).join("")}${"<span></span>".repeat(offset)}${Array.from({ length: count }, (_, i) => `<span class="${i + 1 === now.getDate() ? "now" : (offset + i) % 7 === 0 ? "sun" : ""}">${i + 1}</span>`).join("")}</div>`;
    }
    case "analog": {
      const h = (now.getHours() % 12) + now.getMinutes() / 60,
        m = now.getMinutes() + now.getSeconds() / 60;
      return `<svg class="analog" viewBox="0 0 100 100" aria-label="${esc(now.toLocaleTimeString())}"><circle cx="50" cy="50" r="47" fill="none" stroke="var(--line)" stroke-width="2"/>${[12, 3, 6, 9].map((n, i) => `<text x="${[50, 88, 50, 12][i]}" y="${[16, 53, 91, 53][i]}" text-anchor="middle">${n}</text>`).join("")}<line x1="50" y1="50" x2="50" y2="28" stroke-width="4" transform="rotate(${h * 30} 50 50)"/><line x1="50" y1="50" x2="50" y2="16" stroke-width="2.5" transform="rotate(${m * 6} 50 50)"/><circle cx="50" cy="50" r="3" fill="var(--accent)"/></svg>`;
    }
    case "worldclock":
      return [
        ["서울", "Asia/Seoul"],
        ["도쿄", "Asia/Tokyo"],
        ["런던", "Europe/London"],
        ["뉴욕", "America/New_York"],
      ]
        .map(
          ([n, tz]) =>
            `<div class="row"><span>${n}</span><strong>${now.toLocaleTimeString("en-GB", { timeZone: tz, hour: "2-digit", minute: "2-digit" })}</strong></div>`,
        )
        .join("");
    case "dayprogress": {
      const p =
        ((now - new Date(now.getFullYear(), now.getMonth(), now.getDate())) /
          (new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1) -
            new Date(now.getFullYear(), now.getMonth(), now.getDate()))) *
        100;
      return (
        center(
          Math.floor(p) + "%",
          `자정까지 약 ${Math.ceil(((100 - p) * 24) / 100)}시간`,
        ) + bar("하루", p)
      );
    }
    case "yearprogress": {
      const a = new Date(now.getFullYear(), 0, 1),
        b = new Date(now.getFullYear() + 1, 0, 1),
        p = ((now - a) / (b - a)) * 100;
      return (
        center(
          Math.floor(p) + "%",
          `새해까지 ${Math.ceil((b - now) / 86400000)}일`,
        ) + bar("올해", p)
      );
    }
    case "countdown": {
      const target = cfg.date ? new Date(cfg.date + "T00:00:00") : null;
      if (!target || !Number.isFinite(+target))
        return hint("보관함에서 날짜와 제목을 정해 주세요.");
      const n = Math.ceil(
        (target - new Date(now.getFullYear(), now.getMonth(), now.getDate())) /
          86400000,
      );
      return center(
        n === 0 ? "D-Day" : n > 0 ? "D−" + n : "D+" + Math.abs(n),
        esc(cfg.title || cfg.date),
      );
    }
    case "agenda": {
      const rows = (cfg.events || "")
        .split("\n")
        .map((s) => s.split("|"))
        .filter((r) => r.length === 2 && new Date(r[0].trim()) >= now)
        .sort((a, b) => new Date(a[0]) - new Date(b[0]));
      return rows.length
        ? rows
            .map(
              (r) =>
                `<div class="metric"><strong>${esc(r[1].trim())}</strong><p class="help">${esc(new Date(r[0].trim()).toLocaleString("ko-KR", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }))}</p></div>`,
            )
            .join("")
        : hint("다가오는 일정이 없습니다. 보관함에서 추가하세요.");
    }
    case "cpu":
      return typeof data.cpu !== "number"
        ? hint("시스템 정보를 불러오는 중")
        : center(Math.round(pct(data.cpu)) + "%", "CPU 사용량");
    case "memory":
      return data.memory
        ? center(
            Math.round(pct(data.memory.percent)) + "%",
            esc(bytes(data.memory.used) + " / " + bytes(data.memory.total)),
          )
        : hint("메모리 정보를 불러오는 중");
    case "disk":
      return data.disk
        ? center(
            Math.round(pct(data.disk.percent)) + "%",
            esc(bytes(data.disk.total - data.disk.used) + " 남음"),
          )
        : hint("저장공간 정보를 불러오는 중");
    case "system":
      return data.memory
        ? bar("CPU", data.cpu) +
            bar("메모리", data.memory.percent) +
            bar("저장공간", data.disk?.percent)
        : hint("시스템 정보를 불러오는 중");
    case "network":
      return data.network
        ? `<div class="center"><div class="reading">${esc(bytes(data.network.down))}</div><div class="caption">↓ /s</div><div class="caption">↑ ${esc(bytes(data.network.up))}/s</div></div>`
        : hint("네트워크 정보를 불러오는 중");
    case "uptime":
      return center(
        Math.floor(num(data.uptime) / 3600) + "h",
        `${Math.floor((num(data.uptime) % 3600) / 60)}분 · 부팅 후 경과`,
      );
    case "battery": {
      const items = [
        ...(data.battery
          ? [
              {
                name: data.battery.charging ? "이 PC · 충전 중" : "이 PC",
                percent: data.battery.percent,
                icon: "battery-laptop",
              },
            ]
          : []),
        ...(data.bluetooth || []).map((b) => ({
          ...b,
          icon: "battery-bluetooth",
        })),
      ];
      return items.length
        ? `<div class="battery-grid">${items.map((b) => `<div class="battery-item"><div class="ring"><svg viewBox="0 0 80 80"><circle cx="40" cy="40" r="34"/><circle class="value" cx="40" cy="40" r="34" stroke-dasharray="${pct(b.percent) * 2.136} 214"/></svg><img src="${image(b.icon)}" alt=""></div><div><strong>${Math.round(pct(b.percent))}%</strong><small title="${esc(b.name)}">${esc(b.name)}</small></div></div>`).join("")}</div>`
        : hint(
            "표시 가능한 배터리가 없습니다. Bluetooth 기기는 Windows 드라이버가 배터리를 제공해야 합니다.",
          );
    }
    case "music":
    case "podcast": {
      const m = data.media;
      if (!m || m.status !== "ready")
        return `<div class="center"><img src="${image("music")}" width="44" height="44" alt=""><p class="hint">${m?.status === "error" ? "미디어 세션을 읽을 수 없습니다." : "지원하는 앱에서 음악을 재생하세요."}</p></div>`;
      const art =
        /^data:image\/(png|jpeg|webp|gif);base64,[A-Za-z0-9+/=]+$/.test(
          m.art || "",
        );
      return `<div class="music"><div class="art ${art ? "" : "placeholder"}"><img src="${art ? esc(m.art) : image("music")}" alt="앨범 커버"><button data-action="media" data-command="PlayPause" aria-label="${m.playing ? "일시정지" : "재생"}">${m.playing ? "Ⅱ" : "▶"}</button></div><div class="title">${esc(m.title || "제목 없음")}</div><div class="artist">${esc(m.artist)}</div><div class="playback"><button data-action="media" data-command="Previous" aria-label="이전 곡">◀</button><button data-action="media" data-command="PlayPause" aria-label="재생 또는 일시정지">${m.playing ? "Ⅱ" : "▶"}</button><button data-action="media" data-command="Next" aria-label="다음 곡">▶</button></div></div>`;
    }
    case "weather": {
      if (d?.status !== "ready")
        return hint(
          d?.status === "error"
            ? d.message
            : "보관함에서 도시를 선택해 주세요.",
        );
      const current = d.current,
        daily = d.daily;
      return `<div class="weather"><img class="scene" src="${image("weather-" + weatherName(current.weather_code, current.is_day))}" alt="현재 날씨"><div class="reading">${Math.round(current.temperature_2m)}°</div><div class="caption">${esc(cfg.city || "선택한 위치")}<br>최고 ${Math.round(daily.temperature_2m_max[0])}° · 최저 ${Math.round(daily.temperature_2m_min[0])}°</div><div class="forecast">${daily.time
        .slice(1, 5)
        .map(
          (day, i) =>
            `<div><span>${esc(new Date(day + "T12:00:00").toLocaleDateString("ko-KR", { weekday: "short" }))}</span><img src="${image("weather-" + weatherName(daily.weather_code[i + 1], true))}" alt=""><strong>${Math.round(daily.temperature_2m_max[i + 1])}°</strong></div>`,
        )
        .join("")}</div></div>`;
    }
    case "note":
      return d?.status === "ready"
        ? `<div class="note">${esc(d.text)}</div><button class="open-note" data-action="open" data-id="${c.id}">Obsidian에서 열기 ↗</button>`
        : hint(d?.text || "보관함에서 Markdown 파일을 선택해 주세요.");
    case "todo": {
      const t = data.todo;
      if (!["ready", "cached", "syncing"].includes(t?.status))
        return `<div class="center"><p class="hint">${t?.status === "error" ? "연결을 확인해 주세요." : "todomate 계정을 연결해 주세요."}</p><button data-action="todoLogin">연결 / 열기</button></div>`;
      const task = (row) =>
        `<button class="task ${row.done ? "done" : ""}" data-action="todoToggle" data-task="${esc(row.id)}" data-done="${row.done}" aria-label="${esc(row.text)} · ${row.done ? "완료 취소" : "완료"}" ${(t.pending || []).includes(row.id) ? "disabled" : ""}><span class="check">${row.done ? "✓" : ""}</span><span class="text">${esc(row.text)}</span></button>`;
      const undone = t.tasks.filter((r) => !r.done),
        done = t.tasks.filter((r) => r.done);
      return (
        (t.status === "cached"
          ? hint("오프라인 캐시 · 동기화 대기")
          : t.status === "syncing"
            ? hint("동기화 중…")
            : "") +
        (undone.map(task).join("") || hint("남은 할 일이 없습니다.")) +
        (done.length
          ? `<details id="completed" ${completedOpen ? "open" : ""}><summary>완료한 일 ${done.length}개</summary>${done.map(task).join("")}</details>`
          : "")
      );
    }
    case "focus": {
      const t = d || { remaining: (cfg.minutes || 25) * 60, running: false },
        left = t.running
          ? Math.max(0, Math.ceil((t.endsAt - Date.now()) / 1000))
          : t.remaining;
      return `<div class="center"><div class="big">${String(Math.floor(left / 60)).padStart(2, "0")}:${String(left % 60).padStart(2, "0")}</div><div class="focus-buttons"><button data-action="focus" data-command="toggle">${t.running ? "잠시 멈춤" : "시작"}</button><button data-action="focus" data-command="reset">초기화</button></div></div>`;
    }
    case "screentime": {
      if (!snapshot.state.settings.usage)
        return hint("보관함 → 설정에서 사용 시간 기록을 켜세요.");
      const rows = Object.entries(snapshot.state.usage.apps).sort(
          (a, b) => b[1] - a[1],
        ),
        total = rows.reduce((s, [_n, v]) => s + num(v), 0);
      return `<div class="reading">${total >= 3600 ? Math.floor(total / 3600) + "시간 " : ""}${Math.floor((total % 3600) / 60)}분</div><p class="caption">오늘 · 기록한 시간</p>${rows
        .slice(0, 6)
        .map(([n, v]) =>
          bar(n, (v / (total || 1)) * 100, Math.floor(v / 60) + "분"),
        )
        .join("")}`;
    }
    case "home":
      return d?.status === "ready"
        ? d.entities.length
          ? d.entities
              .map(
                (e) =>
                  `<div class="row"><span>${esc(e.name)}</span>${e.control ? `<button data-action="home" data-entity="${esc(e.id)}">${esc(e.state)}</button>` : `<strong>${esc(e.state)}</strong>`}</div>`,
              )
              .join("")
          : hint("설정한 기기 ID를 확인해 주세요.")
        : hint(d?.message || "보관함에서 내 Home Assistant를 연결하세요.");
    case "kdeconnect":
      return `<div class="center"><img src="${image("bluetooth")}" width="36" height="36" alt=""><button data-action="kdeSend">파일 보내기…</button><p class="caption">KDE Connect · 페어링한 기기</p></div>`;
    default: {
      const m = meta(c.kind);
      return `<button class="launcher" data-action="open" data-id="${c.id}"><img src="${image(c.kind === "sound" ? "sound" : "computer")}" alt=""><strong>${esc(cfg.name || m.name)}</strong><span class="caption">${c.kind === "sound" ? "사운드 설정" : "열기 ↗"}</span></button>`;
    }
  }
}
function renderWidget(animate = false) {
  const g = snapshot.state.groups.find((g) => g.id === groupId);
  if (!g) return;
  const c = g.cards[g.active];
  const previous = document.querySelector(".content")?.scrollTop || 0;
  completedOpen = document.querySelector("#completed")?.open ?? completedOpen;
  const changed = lastActive !== c.id;
  const title =
    c.config.name ||
    (c.kind === "weather" ? c.config.city : null) ||
    meta(c.kind).name;
  const markup = `<article class="card ${target ? "target" : ""}" aria-label="${esc(title)}"><header><span>${esc(title)}</span>${g.cards.length > 1 ? `<button class="stack-count" data-action="cycle" aria-label="다음 위젯">${g.active + 1} / ${g.cards.length}</button>` : ""}</header><div class="content">${renderContent(c)}</div>${["left", "right", "bottom", "left-bottom", "right-bottom"].map((e) => `<div class="edge ${e}" data-edge="${e}"></div>`).join("")}</article>`;
  if (markup === lastMarkup) return;
  lastMarkup = markup;
  app.innerHTML = markup;
  if (!changed) document.querySelector(".content").scrollTop = previous;
  else completedOpen = false;
  if (
    changed &&
    lastActive &&
    animate &&
    !matchMedia("(prefers-reduced-motion: reduce)").matches
  )
    document.querySelector(".content").animate(
      [
        { opacity: 0.25, transform: "translateX(12px)" },
        { opacity: 1, transform: "translateX(0)" },
      ],
      { duration: 200, easing: "cubic-bezier(.2,.7,.2,1)" },
    );
  lastActive = c.id;
}
let signature = "";
function receive(value) {
  if (value.target !== undefined) {
    target = value.target;
    document.querySelector(".card")?.classList.toggle("target", target);
    return;
  }
  if (value.select) {
    editing = value.select;
    selected = allCards().find((c) => c.id === editing)?.kind || selected;
    category = "내 바탕화면";
    renderGallery();
    return;
  }
  snapshot = value;
  document.body.classList.toggle("light", value.theme === "light");
  document.body.classList.toggle("glass", value.state.settings.glass);
  if (groupId) {
    document.body.classList.add("widget");
    if (!dragging) renderWidget(true);
  } else {
    const next = JSON.stringify([
      value.state.groups,
      value.state.settings,
      value.theme,
    ]);
    if (next !== signature) {
      signature = next;
      if (
        !document
          .querySelector("#config-form")
          ?.contains(document.activeElement)
      )
        renderGallery();
    }
  }
}
let dragging = false,
  dragPointer = null;
app.addEventListener("pointerdown", (e) => {
  if (
    !groupId ||
    e.button !== 0 ||
    e.target.closest("button,input,textarea,select,a,summary,.note")
  )
    return;
  dragging = true;
  dragPointer = e.pointerId;
  app.setPointerCapture(e.pointerId);
  call("drag", { mode: e.target.dataset.edge || "move" });
  e.preventDefault();
});
const release = () => {
  if (!dragging) return;
  dragging = false;
  call("drop");
  if (dragPointer !== null && app.hasPointerCapture(dragPointer))
    app.releasePointerCapture(dragPointer);
  dragPointer = null;
};
app.addEventListener("pointerup", release);
app.addEventListener("pointercancel", release);
app.addEventListener("lostpointercapture", release);
window.addEventListener("blur", release);
app.addEventListener("contextmenu", (e) => {
  if (groupId) {
    e.preventDefault();
    call("context");
  }
});
let swipe = 0,
  lastWheel = 0,
  lastCycle = 0;
app.addEventListener(
  "wheel",
  (e) => {
    if (!groupId) return;
    const dx =
      Math.abs(e.deltaX) > Math.abs(e.deltaY)
        ? e.deltaX
        : e.shiftKey
          ? e.deltaY
          : 0;
    if (!dx) return;
    const g = snapshot.state.groups.find((g) => g.id === groupId);
    if (g?.cards.length < 2) return;
    e.preventDefault();
    const now = Date.now();
    if (now - lastWheel > 180) swipe = 0;
    lastWheel = now;
    if (now - lastCycle < 550) return;
    swipe += dx * (e.deltaMode === 1 ? 16 : 1);
    if (Math.abs(swipe) > 65) {
      lastCycle = now;
      call("cycle", { direction: swipe > 0 ? 1 : -1 });
      swipe = 0;
    }
  },
  { passive: false },
);
app.addEventListener("click", async (e) => {
  const b = e.target.closest("[data-action]");
  if (!b) return;
  const a = b.dataset.action;
  if (a === "category") {
    category = b.dataset.category;
    editing = null;
    renderGallery();
  }
  if (a === "select") {
    selected = b.dataset.kind;
    editing = null;
    cities = [];
    renderGallery();
  }
  if (a === "edit") {
    editing = b.dataset.id;
    renderGallery();
  }
  if (a === "remove") {
    await call("remove", { card: editing });
    editing = null;
    renderGallery();
  }
  if (a === "removeCard") await call("remove", { card: b.dataset.id });
  if (a === "pickNote") {
    const file = await call("pickNote");
    if (file) document.querySelector("[name=notePath]").value = file;
  }
  if (a === "cities") {
    const form = document.querySelector("#config-form");
    cities = (await call("cities", { query: form.elements.city.value })) || [];
    const parent = b.parentElement;
    const results = parent.querySelector(".city-results");
    results.innerHTML =
      cities
        .map(
          (v, i) =>
            `<button type="button" data-action="chooseCity" data-index="${i}">${esc(v.name)} · ${esc(v.admin1 || v.country || "")}</button>`,
        )
        .join("") ||
      '<p class="help">검색 결과가 없습니다. 영문 이름으로 시도해 보세요.</p>';
  }
  if (a === "chooseCity") {
    const c = cities[Number(b.dataset.index)],
      f = document.querySelector("#config-form");
    f.elements.city.value = c.name;
    f.elements.latitude.value = c.latitude;
    f.elements.longitude.value = c.longitude;
    f.querySelector(".city-results").innerHTML = "";
  }
  if (a === "todoLogin") await call("todoLogin");
  if (a === "todoDisconnect") await call("todoDisconnect");
  if (a === "open") await call("open", { id: b.dataset.id });
  if (a === "cycle") await call("cycle", { direction: 1 });
  if (a === "media") await call("media", { command: b.dataset.command });
  if (a === "todoToggle")
    await call("todoToggle", {
      id: b.dataset.task,
      done: b.dataset.done === "true",
      date: snapshot.data.todo.date,
    });
  if (a === "home") {
    const g = snapshot.state.groups.find((g) => g.id === groupId);
    await call("home", { id: g.cards[g.active].id, entity: b.dataset.entity });
  }
  if (a === "focus") {
    const g = snapshot.state.groups.find((g) => g.id === groupId);
    await call("focus", {
      id: g.cards[g.active].id,
      command: b.dataset.command,
    });
  }
  if (a === "kdeSend") {
    const devices = await call("devices");
    if (!devices?.length) {
      toast(
        "사용 가능한 기기가 없습니다. KDE Connect 설치와 페어링을 확인해 주세요.",
      );
      return;
    }
    const content = document.querySelector(".content");
    content.innerHTML = `<p class="help">보낼 기기를 선택하세요.</p>${devices.map((id) => `<button class="task" data-action="sendTo" data-device="${esc(id)}">${esc(id)}</button>`).join("")}`;
  }
  if (a === "sendTo") {
    await call("send", { device: b.dataset.device });
  }
});
app.addEventListener("submit", async (e) => {
  if (e.target.id !== "config-form") return;
  e.preventDefault();
  const form = new FormData(e.target),
    cfg = Object.fromEntries(form);
  size = cfg.size || size;
  delete cfg.size;
  const token = cfg.token;
  delete cfg.token;
  if (editing) {
    const result = await call("update", { id: editing, config: cfg, token });
    if (result) toast("설정을 저장했습니다.");
  } else {
    const result = await call("add", {
      kind: selected,
      config: cfg,
      size,
      token,
    });
    if (result) toast("바탕화면에 추가했습니다.");
  }
});
app.addEventListener("change", (e) => {
  if (e.target.id === "theme") call("settings", { theme: e.target.value });
  if (e.target.dataset.setting)
    call("settings", { [e.target.dataset.setting]: e.target.checked });
});
app.addEventListener("input", (e) => {
  if (e.target.id === "search") {
    query = e.target.value;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      renderGallery();
      const s = document.querySelector("#search");
      s.focus();
      s.setSelectionRange(query.length, query.length);
    }, 180);
  }
});
api.subscribe(receive);
api
  .invoke("snapshot")
  .then(receive)
  .catch((e) => toast(e.message));
setInterval(() => {
  if (groupId && snapshot && !dragging) renderWidget(false);
}, 1000);
