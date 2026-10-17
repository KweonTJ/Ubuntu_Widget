# Ubuntu Widget

**English** | [한국어](README.ko.md)

[![Package checks](https://github.com/KweonTJ/Ubuntu_Widget/actions/workflows/ci.yml/badge.svg)](https://github.com/KweonTJ/Ubuntu_Widget/actions/workflows/ci.yml)

A macOS-inspired desktop widget library for **Ubuntu GNOME on Xorg**. Browse **34 built-in choices**, add individual widgets, and place them on a 16 px grid. Cards share rounded corners, responsive layouts, light/dark themes, and optional glass effects.

This is an independent community project, not an Apple product. The current on-screen interface is primarily Korean; the setup labels used below include their original text. A Korean README is available through the language link above; additional documentation is in English.

![Widget Library rendered with clean defaults](docs/images/widget-library.png)

*Clean-profile preview; card metrics are illustrative. No personal desktop or account content is shown.*

## Ubuntu support

| Environment | Status |
| --- | --- |
| **Ubuntu 22.04 LTS, GNOME 42, Xorg, x86-64** | **Verified desktop environment** (tested on 22.04.5 LTS). Movement, deletion, resizing, themes and desktop-icon stacking were exercised here. |
| Ubuntu 24.04 LTS, GNOME 46, **Xorg** | **Experimental / not desktop-verified.** Build from source and use a matching Blur my Shell version if you need blur. Automated package checks do not establish full desktop compatibility. |
| Ubuntu 20.04 or older | Unsupported by this package; the default Python version is too old. |
| Ubuntu Desktop 25.10 and newer, including 26.04 LTS, default GNOME session | Unsupported: these GNOME sessions are Wayland-only. XWayland is not a replacement for a full Xorg session for this package. |
| Wayland sessions, other desktop environments or CPU architectures | Not verified or supported by this release. |

**The verified support claim currently stops at Ubuntu 22.04.** Ubuntu 24.04 is an experimental target, not a promise of compatibility. See the [official Ubuntu GNOME/Xorg announcement](https://discourse.ubuntu.com/t/ubuntu-25-10-drops-support-for-gnome-on-xorg/62538) and [26.04 LTS release notes](https://documentation.ubuntu.com/release-notes/26.04/summary-for-lts-users/) for the Wayland transition.

Check your session before installing:

```bash
echo "$XDG_SESSION_TYPE"  # must print x11
```

On supported Ubuntu installations, choose **Ubuntu on Xorg** from the login-screen session menu if needed. Do not install this package expecting the native desktop controls to work under Wayland.

## Install

Runtime requirements: Python 3.10+, GTK 3, a full GNOME/Xorg session, and a working user systemd/D-Bus session.

Install runtime and build dependencies through Ubuntu's package manager:

```bash
sudo apt update
sudo apt install git build-essential pkg-config libgtk-3-dev libdbusmenu-gtk3-dev \
  python3 python3-gi python3-gi-cairo python3-cairo python3-dbus \
  gir1.2-gtk-3.0 gir1.2-secret-1 gnome-keyring libx11-6 libxss1 \
  pulseaudio-utils libnotify-bin xdg-utils fonts-noto-cjk
```

Install a current stable Rust toolchain using [rustup's official instructions](https://rustup.rs/). Rust is needed to build the patched Eww engine, not for ordinary use afterwards.

```bash
git clone https://github.com/KweonTJ/Ubuntu_Widget.git
cd Ubuntu_Widget
./scripts/build-eww.sh
./install.sh
"$HOME/.local/bin/ubuntu-widget" edit
```

- `build-eww.sh` fetches Eww commit `48f5aa8b379adf29da0b0bb9ca04164f65d8bdaa`, checks and applies our native-control patch, and builds only its X11 backend. The script uses the installed **stable** Rust toolchain instead of the old toolchain pinned by upstream. `RUST_TOOLCHAIN` can select another installed toolchain.
- A stock Eww binary does **not** implement the custom drag/resize attributes used by these widgets. Do not replace the patched engine with a distribution Eww package.
- This repository distributes source and the patch, not a copy of a developer's local executable or desktop backup. The initial desktop engine was verified with stable Rust 1.99.0 on Ubuntu 22.04.
- If a build runs out of memory, retry with `CARGO_BUILD_JOBS=2 ./scripts/build-eww.sh`.
- To use an already built **patched** binary, run `./install.sh --eww /path/to/eww`.
- Add `--autostart` to install a login entry for widgets you have added. Autostart is otherwise off.
- Installation is per-user and needs no `sudo`. It does not overwrite an unrelated Eww setup.

Open **Widget Library / 위젯 보관함** from the application menu. A fresh installation starts with an empty desktop; select the widgets you want and click **바탕화면에 추가** (Add to desktop). Add-ons that require an account display a setup prompt until you connect your own account.

## Included widgets

| Category | Choices |
| --- | --- |
| Time and date (9) | Digital clock, calendar, analog clock, upcoming events, world clocks, today's date, day progress, year progress, countdown |
| Notes and focus (3) | Note, to-do list, focus timer |
| System (8) | System overview, battery, screen time, CPU, memory, storage, network speed, uptime |
| Media (3) | Music, volume, podcasts |
| Weather and home (2) | Weather, Home Assistant |
| Stocks (1) | Toss Securities watchlist and market indices |
| Website shortcuts (8) | Notion, Naver Mail, Gmail, Google Calendar, Google Keep, YouTube, Spotify, GitHub |

Website choices are launchers: they open the website, rather than embedding a signed-in page inside an Eww card. You can register additional URLs. Chrome or Chromium opens a standalone app window; other systems fall back to their default browser with `xdg-open`.

## Move, resize and remove

- **Move:** drag the **inside upper-right corner** of a widget. Movement snaps to a 16 px grid.
- **Change width:** drag the right edge.
- **Change width and height:** drag the inside lower-right corner.
- **Remove:** click the **inside upper-left corner**, or use the right-click menu / library. The X icon and grip marks are intentionally invisible.
- **Restore:** add the widget again from the library. Removing a card does not delete its saved content.
- **Sizes:** Small `208 × 208`, Medium `320 × 224`, Large `432 × 352`; minimum `192 × 96` logical pixels. Scroll inside short cards to reach overflow content.
- Narrow cards arrange their contents vertically. The calendar starts on **Sunday**.
- Transparent desktop-icon windows are kept beneath the widget cards so they cannot block the controls. Widgets remain below normal application windows.

## Widgets that need your settings

Use **내용·시간 설정** (Content/time settings) or **연결·설정** (Connection/settings) in the selected widget's detail panel.

### Stocks — Toss Securities

- Open your own [Toss Securities WTS](https://www.tossinvest.com/), then **Settings → Open API**.
- Create your **Client ID / Client Secret** and register your current **public IP address** in the allowed-IP settings.
- In the library, select **주식 · 토스증권 → 연결·설정**. Enter the credentials directly in the masked fields and choose **연결 확인 및 저장** (Test and save).
- Enter watchlist symbols separated by commas, e.g. `005930,AAPL`; optionally enter index symbols such as `KOSPI,KOSDAQ`. Up to 12 stock symbols and 12 indicator symbols are accepted, subject to the provider's supported symbols.
- Use **관심 목록만 저장** to edit the list without entering your keys again. Use **연결 해제 · 저장된 키 삭제** to remove this application's saved credentials.
- Credentials and the reusable access token live in **GNOME Keyring / Secret Service**. There is no plaintext credential fallback.
- Quotes refresh through the REST API every **30 seconds**, while the card is added. Source-data and fetch times are shown. This is not tick-by-tick streaming. A previous-close percentage is shown only when comparable candle data is available.
- This integration does not query balances or place orders. It makes authentication and public market-data requests only.
- Toss allows one valid token per client. Use a separate API client for other programs to avoid invalidating each other's tokens. If your public IP changes, update the provider's allowlist.
- No shared keys are supplied. API access and terms are controlled by Toss. See the [official API guide](https://developers.tossinvest.com/docs).

### Weather

- Select **날씨 → 연결·설정**, search for a city, choose the correct result and save it.
- No automatic location tracking is used. Search terms and selected coordinates are sent to Open-Meteo.
- Shows current temperature, daily low/high, the next six hourly forecasts, a seven-day forecast, US AQI and PM2.5; refreshes every **15 minutes** while the card is added.
- Air-quality values are CAMS-based predictions. US AQI is not the Korean integrated air-quality index.
- The bundled adapter uses Open-Meteo's public non-commercial endpoint. Commercial deployments must arrange an appropriate service plan/adapter and follow the [provider's terms](https://open-meteo.com/en/terms).
- Attribution: **Weather data by Open-Meteo (CC BY 4.0); air-quality data by CAMS / Open-Meteo**. See [weather](https://open-meteo.com/en/docs) and [air-quality](https://open-meteo.com/en/docs/air-quality-api) documentation.

### Home — Home Assistant

- Register your devices in your own Home Assistant server first.
- In your Home Assistant profile, create a long-lived access token. Enter the server's base URL, token and entity IDs in **홈 → 연결·설정**.
- Example URL: `http://homeassistant.local:8123`. Example entities: `light.living_room,sensor.temperature`.
- HTTP is limited to local-network addresses; use HTTPS for an external server. Tokens are saved in GNOME Keyring.
- Up to 12 `light`, `switch`, `sensor`, `binary_sensor` or `climate` entities can be displayed. Status refreshes every **30 seconds** while added.
- Lights and switches can be turned on/off from the card. Sensors and thermostats are read-only in this release.
- This is a Home Assistant connection, not a direct Apple HomeKit account connection. See the [REST API documentation](https://developers.home-assistant.io/docs/api/rest/).

### Notes, tasks, dates and focus

- **Note / 메모:** enter a title and up to 2,000 characters. Useful for a short daily reference.
- **To-do / 할 일:** enter one task per line, up to 12 tasks. Click a task on the desktop to check it off.
- **Upcoming events / 다가오는 일정:** enter one event per line as `YYYY-MM-DD HH:MM | Event title`, up to 40 entries. The next 12 are shown. These are local events, without Google/Apple account sync or event alarms.
- **Countdown / 디데이:** choose a title and date in `YYYY-MM-DD` format.
- **Focus / 집중 타이머:** choose 1–180 minutes; start, pause or reset from the widget. Completion notifications require the timer's data listener to be running.
- Digital/analog clocks and local events use your **system timezone**. World clocks ship with public sample cities; change their IANA timezone list in your user configuration as described in [configuration](docs/CONFIGURATION.md).

### Screen time

- Recording is **off by default**. Enable it yourself in **스크린 타임 → 기록 설정**.
- Counts the active application's class/name every five seconds while at least one desktop card is open. It does not store window titles, document names or URLs.
- Excludes the locked session, extended idle periods and suspend gaps. This is sampled usage, not an exact audit log.
- Shows today's total and the top eight apps. Up to 30 days of local usage data are retained; the settings dialog can stop or clear recording.

### Media and Bluetooth batteries

- Start playback in a player/browser that supports **MPRIS**. Music and podcast cards show the active session and available controls; there is no bundled player or podcast directory.
- Bluetooth battery levels require connected devices that expose **BlueZ Battery1** or matching **UPower** data. Missing levels are shown as `—`, not invented.
- Sound controls require `pactl` and a working PulseAudio or PipeWire PulseAudio-compatible session.

### Your own websites

- Click **＋ 웹사이트**, enter a name and an `https://` URL, then add the shortcut.
- Log in through the website's own browser window. The widget library does not read or export browser cookies.
- Useful for dashboards, mail, calendars or an internal service. Keep private URLs in your installed configuration, not in Git.

## Themes and glass

- The library's theme selector can follow the system, or use light/dark explicitly.
- Glass effects start **off** in the public package. Enable **글래스 효과 → 전체 위젯** for all widgets, or adjust the per-widget switch.
- Real backdrop blur requires a compatible [Blur my Shell](https://github.com/aunetx/blur-my-shell) extension. **Version 47 / GNOME 42** was verified. The extension is optional and is not bundled or automatically installed.
- On other GNOME/extension versions, blur is unverified; the translucent card styling can still work. Unsupported schema versions are skipped.
- While real blur is active, the integration temporarily changes the extension's application-blur, opacity and redraw-workaround settings; it restores saved values when the last effect is disabled, unless another application changed them. Turn glass off before uninstalling.
- No macOS wallpaper, theme, font, icon pack or Apple software is included.

## Personal data and storage

The published defaults contain **no personal notes, events, watchlists, device IDs, private URLs, coordinates, window positions, API keys, browser data, usage history, recordings or local executables**.

| Data | Installed location |
| --- | --- |
| Configuration and local content | `${XDG_CONFIG_HOME:-~/.config}/ubuntu-widget/` |
| Logs and usage history | `${XDG_CACHE_HOME:-~/.cache}/ubuntu-widget/` |
| API credentials | GNOME Keyring / Secret Service, namespaced to the configuration path |
| Patched engine | `~/.local/lib/ubuntu-widget/eww` |
| Launcher | `~/.local/bin/ubuntu-widget` |

There is no analytics endpoint. Network traffic is limited to providers you connect/configure and websites you explicitly open. Do not commit your installed configuration or create public archives from it. See [privacy details](docs/PRIVACY.md).

## Update, uninstall and troubleshoot

```bash
git pull --ff-only
./scripts/build-eww.sh
./install.sh
"$HOME/.local/bin/ubuntu-widget" restart
```

Installation preserves existing notes, accounts, websites, layout and other user-state files. Program files and default styles are replaced; keep custom styles in a separate backup before upgrading.

```bash
./scripts/uninstall.py
```

Uninstall keeps personal configuration and keyring entries. Disconnect accounts and turn glass off in the app first if you want credentials removed and compositor preferences restored. Remove your local config/cache manually only when you intend to erase your own content.

If the app does not launch, check the cache directory's `gallery.log` and `daemon.log`. Verify Xorg, the patched engine, a running user systemd/D-Bus session, and an unlocked GNOME Keyring. If controls stop responding, restart the engine; its layout listener also repairs desktop-icon stacking automatically.

The Apple iPhone Continuity widget system is **not available on Ubuntu**. Website shortcuts are provided for services with a web interface; they do not mirror iPhone apps.

## Open-source components

| Component | Role | License / source |
| --- | --- | --- |
| [Eww](https://github.com/elkowar/eww) | Widget renderer; pinned source plus our native movement/resize patch | MIT; [included notice](LICENSES/Eww-MIT.txt) |
| [GTK 3](https://www.gtk.org/), GLib/GIO and GDK | Native library, dialogs, themes and desktop integration | LGPL; system dependencies |
| [PyGObject](https://pygobject.gnome.org/) | Python bindings for GTK/GIO/libsecret | LGPL-2.1-or-later |
| [Cairo / Pycairo](https://pycairo.readthedocs.io/) | Widget-library preview drawing | Upstream LGPL/MPL licenses |
| [D-Bus / dbus-python](https://www.freedesktop.org/wiki/Software/dbus/) | Session services, media, battery and keyring communication | Upstream D-Bus and dbus-python licenses |
| [libsecret](https://gnome.pages.gitlab.gnome.org/libsecret/) / [GNOME Keyring](https://gitlab.gnome.org/GNOME/gnome-keyring) | Secret storage | Upstream LGPL/GPL licenses |
| [Blur my Shell](https://github.com/aunetx/blur-my-shell) | Optional real background blur | GPL-3.0-or-later; not bundled |
| [BlueZ](https://www.bluez.org/) / [UPower](https://upower.freedesktop.org/) | Bluetooth and system battery data | Upstream GPL/LGPL licenses; system services |
| [PulseAudio](https://www.freedesktop.org/wiki/Software/PulseAudio/), or [PipeWire](https://pipewire.org/) compatibility | Volume controls through `pactl` | System services, not bundled |
| [Python](https://www.python.org/), [X.Org](https://www.x.org/), [systemd](https://systemd.io/) | Runtime, X11 control and user services | Respective upstream licenses |
| [Noto CJK](https://github.com/notofonts/noto-cjk) | Recommended CJK-capable system font | SIL Open Font License |

Toss, Open-Meteo and Home Assistant HTTP endpoints are **external service integrations**, not bundled stock-data services. Public website presets are URLs, not copies of those applications. Chromium is an optional open-source browser; proprietary Google Chrome is an optional user-installed alternative. See [third-party notices](THIRD_PARTY_NOTICES.md) for provenance and license links.

This repository's original configuration, scripts, native patch and SVG artwork are available under the [MIT License](LICENSE). Upstream projects retain their own copyrights and licenses.

## Development checks

```bash
/usr/bin/python3 -m unittest discover -s tests -v
/usr/bin/python3 scripts/check_public.py
```

See [validation scope](docs/VALIDATION.md) for the desktop checks actually performed. CI checks the package on Ubuntu 22.04 and 24.04. These checks cover blank defaults, installation under different user paths, configuration preservation, API adapters with mock data and source-patch applicability. They do not replace desktop testing on each GNOME release.
