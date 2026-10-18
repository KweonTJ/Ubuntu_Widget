# Ubuntu Widget · Windows Widget

**English** · [한국어](README.ko.md)

[![Release](https://img.shields.io/github/v/release/KweonTJ/Ubuntu_Widget)](https://github.com/KweonTJ/Ubuntu_Widget/releases/latest)
[![Package checks](https://github.com/KweonTJ/Ubuntu_Widget/actions/workflows/ci.yml/badge.svg)](https://github.com/KweonTJ/Ubuntu_Widget/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Desktop widgets for **Ubuntu GNOME on Xorg**. Choose from 35 widgets and website shortcuts, arrange them on a grid, and match your desktop with light/dark themes and optional glass.

A separate **Windows 11 x64 edition** is available in [`windows-widget/`](windows-widget/README.md). [Windows installation](#windows-11) · [Windows release](https://github.com/KweonTJ/Ubuntu_Widget/releases/tag/windows-v1.0.0).

Drag matching widgets together to stack them. Switch cards with a **two-finger horizontal swipe** on the trackpad.

[Install](#install) · [Releases](#releases) · [Desktop controls](#desktop-controls) · [Stacks and gestures](#stacks-and-gestures) · [Connect your apps](#widgets-that-need-your-settings) · [Ubuntu support](#ubuntu-support)

![Widget Library with clean defaults](docs/images/widget-library.png)

*Clean-profile preview with illustrative data. The current app interface is primarily Korean. This is an independent project, not an Apple product.*

## Install

Widget Library is a native desktop app. After installation, open **Widget Library** from the application menu, then right-click its dock icon and choose **Add to Favorites**. The dock icon opens the library to add and manage widgets; your placed widgets remain on the desktop.

### Recommended: install the Debian package

Download `ubuntu-widget_2.2.0-1_amd64.deb` from [Ubuntu v2.2.0 release](https://github.com/KweonTJ/Ubuntu_Widget/releases/tag/v2.2.0). Open a terminal in the download folder and run:

```bash
sudo apt install ./ubuntu-widget_2.2.0-1_amd64.deb
/usr/bin/ubuntu-widget
```

APT installs the required runtime dependencies. **Rust and build tools are not required**: the patched Eww engine is included. Open **Widget Library / 위젯 보관함** from the application menu afterwards. Use Ubuntu 22.04 amd64 with an Xorg session; the [Ubuntu support](#ubuntu-support) limits also apply to the Debian package.

The first launch creates your own configuration with an empty desktop. Package installation does not copy the developer's settings, access accounts, or enable autostart. Updates refresh program templates on your next launch and preserve notes, connections and layout. If you previously installed from source, remove that installation's launcher with `./scripts/uninstall.py` before switching to the Debian package; your configuration is kept.

Release assets also include `SHA256SUMS` and the matching `*-source.tar.xz` archive containing patched Eww and vendored Cargo sources. See [packaging and rebuilding](docs/PACKAGING.md).

### Windows 11

1. Download the [Windows installer EXE](https://github.com/KweonTJ/Ubuntu_Widget/releases/download/windows-v1.0.0/windows-widget-1.0.0-x64-win.exe) from [Windows v1.0.0](https://github.com/KweonTJ/Ubuntu_Widget/releases/tag/windows-v1.0.0) and run it on **Windows 11 x64, build 22000 or later**. Windows 10 is not supported. Node.js, Python, Eww and administrator rights are not needed for the installer.
2. Choose an installation directory, then open **Widget Library** from the Start menu or desktop shortcut. Select a widget and click **바탕화면에 추가**. Right-click the library's taskbar icon to pin it.
3. Alternatively, extract the entire [portable ZIP](https://github.com/KweonTJ/Ubuntu_Widget/releases/download/windows-v1.0.0/windows-widget-1.0.0-x64-win.zip) and run **Widget Library.exe**. Keep all extracted runtime files together.
4. Closing the library leaves widgets running in the tray. Use the tray menu to reopen it, show all widgets or exit. Enable login startup in **설정** if wanted.

This is an **initial prerelease**. The binaries are unsigned, so Windows may show an unrecognized-publisher prompt. Windows 11 hardware, account and gesture integrations are not fully validated; see the [Windows guide](windows-widget/README.md) and [validation status](windows-widget/docs/VALIDATION.md). Toss Securities is a website shortcut in the Windows edition. User settings stay in `%APPDATA%\windows-widget\` and are preserved on uninstall. No personal settings or login data are shipped.

The Windows source lives in `windows-widget/`; Ubuntu's Eww/GTK engine is separate. The desktop controls and provider details below describe the Ubuntu edition; consult the Windows guide for platform differences.

## Desktop controls

| Action | How |
| --- | --- |
| Add | Open **Widget Library / 위젯 보관함**, pick a widget and choose **바탕화면에 추가**. |
| Move | Drag the widget body. Placement snaps to a 16 px grid. |
| Resize | Drag either side to change width; drag anywhere along the bottom edge to change height. Dimensions snap to a 16 px grid. |
| Stack | Drop a card over the middle of another card with the same width and height. |
| Switch a stack | Swipe horizontally with two fingers over the card, or click/scroll its page counter. |
| Split | Right-click → **스택 해제**, or use the library detail panel. |
| Remove | Click the invisible inside upper-left corner, or remove it from the context menu/library. |
| Restore | Add it again from the library; its saved content is preserved. |

Presets: Small **208 × 208**, Medium **320 × 224**, Large **432 × 352**. The minimum is **192 × 96** logical pixels. Short cards keep overflow content scrollable; narrow cards adapt their layout. Calendars start on Sunday.

## Stacks and gestures

1. Give two widgets the same width and height. Choosing the same preset in the library is the quickest way.
2. Drag one card over the other. A blue outline marks a matching drop target when the cards overlap by at least 65%.
3. Release to create the stack at the target's position. Dropping onto an existing stack adds the card; dropping one stack onto another combines their members.
4. Swipe horizontally with two fingers anywhere over the stack to switch. One continuous stroke advances one card. Vertical two-finger scrolling continues to scroll the widget's content.

The page counter remains available for mouse clicks and wheel input. Moving or resizing a stack keeps one shared placement and size, and restarting keeps the last active card. **스택 해제** restores each card's placement from before it joined the stack.

Use two-finger scrolling enabled in your system's touchpad settings. Switching follows the horizontal scroll direction supplied by the system, including its natural-scrolling preference.

## Releases

Versioned packages and detailed change notes are maintained in [GitHub Releases](https://github.com/KweonTJ/Ubuntu_Widget/releases).

| Version | Highlights |
| --- | --- |
| [Windows v1.0.0](https://github.com/KweonTJ/Ubuntu_Widget/releases/tag/windows-v1.0.0) | Initial Windows 11 library, independent cards, grid resizing, stacks, themes and Windows adapters (prerelease). |
| [v2.2.0](https://github.com/KweonTJ/Ubuntu_Widget/releases/tag/v2.2.0) | Album covers, weather icons, completed-task folding, full-width height resizing and responsive fixes. |
| [v2.1.1](https://github.com/KweonTJ/Ubuntu_Widget/releases/tag/v2.1.1) | Smooth stack transitions with stable window position and size. |
| [v2.1.0](https://github.com/KweonTJ/Ubuntu_Widget/releases/tag/v2.1.0) | Drag-to-stack, stack merging and trackpad gestures. |
| [v2.0.0](https://github.com/KweonTJ/Ubuntu_Widget/releases/tag/v2.0.0) | Redesigned widget library, app connections and widget stacks. |
| [v0.1.1](https://github.com/KweonTJ/Ubuntu_Widget/releases/tag/v0.1.1) | Debian installer and matching source distribution. |

## Included widgets

| Category | Choices |
| --- | --- |
| Time and date (9) | Digital clock, calendar, analog clock, upcoming events, world clocks, today's date, day progress, year progress, countdown |
| Notes and focus (3) | Note, to-do list, focus timer |
| System (9) | System overview, battery, screen time, CPU, memory, storage, network speed, uptime, KDE Connect file sharing |
| Media (3) | Music, volume, podcasts |
| Weather and home (2) | Weather, Home Assistant |
| Stocks (1) | Toss Securities watchlist and market indices |
| Website shortcuts (8) | Notion, Naver Mail, Gmail, Google Calendar, Google Keep, YouTube, Spotify, GitHub |

Website choices are launchers: they open the website, rather than embedding a signed-in page inside an Eww card. You can register additional URLs. Chrome or Chromium opens a standalone app window; other systems fall back to their default browser with `xdg-open`.

## Widgets that need your settings

Use **내용·시간 설정** (Content/time settings) or **연결·설정** (Connection/settings) in the selected widget's detail panel.

### Music — album artwork

- The music card reads the current player's [MPRIS artwork URL](https://specifications.freedesktop.org/mpris/latest/Track_List_Interface.html#Mapping:Metadata_Map). Local files and HTTP(S) covers are cached as small, rounded thumbnails; a changed track refreshes its artwork.
- Players that do not provide artwork keep the music icon. No account setup is required.
- A large cover sits above the song title and, when space allows, the artist. Short cards put play/pause on the cover; taller cards add previous/next controls below. Artwork is cached at 512 px for crisp display at 2× scaling.

### KDE Connect — file sharing

- Install KDE Connect on the PC (`sudo apt install kdeconnect`) and the other device, then pair them in KDE Connect. This is an optional dependency.
- Keep both devices reachable and enable the **Share and receive** plugin.
- Add **KDE Connect · 파일 공유** from the library. Click **파일 보내기…**, choose the receiving device, select files (or drop them into the sending window), and click **보내기**.
- Multiple files are supported; compress folders before selecting them. Files are sent only when you click Send. Transfer completion and received files are managed by KDE Connect.
- No device IDs, selected file paths, or transfer history are saved by the widget.

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
- A prominent condition icon aligns with the current temperature; its size follows the card dimensions and its artwork follows local daylight and the light/dark theme. Compact cards prioritize current conditions; taller cards add scrollable forecasts. Open the library or the widget context menu to change the location.
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

- **Obsidian notes:** choose a Markdown file from an Obsidian-registered vault using **노트 선택…**. The card reads it locally and follows edits; **Obsidian에서 열기** opens the same note through the official Obsidian URI. The widget never writes to the note.
- **todomate tasks:** choose **todomate 연결…** and sign in to the official website once. The native card shows today's own tasks and lets you check/uncheck them. Completed tasks move to a collapsed section at the bottom; expand it to review them or undo completion. One local WebKit session supplies the page's authenticated Firebase client; no passwords or tokens are copied to the widget or sent to a relay. This is an **unofficial compatibility adapter**, not a documented todomate API, and may need updates if its web app changes. Active timed tasks are completed in the official app. Chrome and the widget have separate login storage.
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

The todomate profile is stored under `.web-profile/todomate/` inside your user configuration. It contains sensitive login data: never commit, export or share that directory. Obsidian note paths live in `linked-apps.json`; no note content is copied into the package. On Ubuntu 24.04 source installations, install `gir1.2-webkit2-4.1` instead of the 22.04 WebKit package shown above.

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

## Build from source

<details>
<summary>Build the patched Eww engine and install per user</summary>

Runtime requirements: Python 3.10+, GTK 3, a full GNOME/Xorg session, and a working user systemd/D-Bus session.

Install runtime and build dependencies through Ubuntu's package manager:

```bash
sudo apt update
sudo apt install git build-essential pkg-config libgtk-3-dev libdbusmenu-gtk3-dev \
  python3 python3-gi python3-gi-cairo python3-cairo python3-dbus tzdata \
  gir1.2-gtk-3.0 gir1.2-webkit2-4.0 gir1.2-secret-1 gnome-keyring libx11-6 libxss1 libxtst6 \
  gsettings-desktop-schemas dconf-gsettings-backend librsvg2-common x11-utils \
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
- The Git repository contains source and the patch. Release Debian packages include an engine built from that source, without a developer's desktop backup. The initial desktop engine was verified with stable Rust 1.99.0 on Ubuntu 22.04.
- If a build runs out of memory, retry with `CARGO_BUILD_JOBS=2 ./scripts/build-eww.sh`.
- To use an already built **patched** binary, run `./install.sh --eww /path/to/eww`.
- Add `--autostart` to install a login entry for widgets you have added. Autostart is otherwise off.
- Installation is per-user and needs no `sudo`. It does not overwrite an unrelated Eww setup.

Open **Widget Library / 위젯 보관함** from the application menu. A fresh installation starts with an empty desktop; select the widgets you want and click **바탕화면에 추가** (Add to desktop). Add-ons that require an account display a setup prompt until you connect your own account.

</details>

## Personal data and storage

The published defaults contain **no personal notes, events, watchlists, device IDs, private URLs, coordinates, window positions, API keys, browser data, usage history, recordings or local executables**.

| Data | Installed location |
| --- | --- |
| Configuration and local content | `${XDG_CONFIG_HOME:-~/.config}/ubuntu-widget/` |
| Logs and usage history | `${XDG_CACHE_HOME:-~/.cache}/ubuntu-widget/` |
| API credentials | GNOME Keyring / Secret Service, namespaced to the configuration path |
| Patched engine | Debian: `/usr/lib/ubuntu-widget/eww`; source install: `~/.local/lib/ubuntu-widget/eww` |
| Launcher | Debian: `/usr/bin/ubuntu-widget`; source install: `~/.local/bin/ubuntu-widget` |
| Debian package templates | `/usr/share/ubuntu-widget/` (copied into each user's configuration on first launch) |

There is no analytics endpoint. Network traffic is limited to providers you connect/configure and websites you explicitly open. Do not commit your installed configuration or create public archives from it. See [privacy details](docs/PRIVACY.md).

## Update, uninstall and troubleshoot

For the Debian package, download the new `.deb` and install it with `sudo apt install ./<downloaded-file>.deb`, then run `/usr/bin/ubuntu-widget restart`. To remove its program files, use `sudo apt remove ubuntu-widget`. User configuration and keyring entries are preserved, including when the package is purged. Disconnect accounts and turn glass off in the app before removing it if you want credentials deleted and compositor preferences restored. Autostart is opt-in; if you configured a startup entry yourself, remove that entry too.

For a source installation:

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

No iPhone connection controls or Continuity setup are included. Native Apple Continuity is not implemented.

## Open-source components

| Component | Role | License / source |
| --- | --- | --- |
| [Eww](https://github.com/elkowar/eww) | Widget renderer; pinned source plus our native movement/resize patch | MIT; [included notice](LICENSES/Eww-MIT.txt) |
| [WebKitGTK](https://webkitgtk.org/) | Local todomate login and task bridge | System LGPL/BSD dependency; not bundled |
| [GTK 3](https://www.gtk.org/), GLib/GIO and GDK | Native library, dialogs, themes and desktop integration | LGPL; system dependencies |
| [PyGObject](https://pygobject.gnome.org/) | Python bindings for GTK/GIO/libsecret | LGPL-2.1-or-later |
| [Cairo / Pycairo](https://pycairo.readthedocs.io/) | Widget-library preview drawing | Upstream LGPL/MPL licenses |
| [D-Bus / dbus-python](https://www.freedesktop.org/wiki/Software/dbus/) | Session services, media, battery and keyring communication | Upstream D-Bus and dbus-python licenses |
| [libsecret](https://gnome.pages.gitlab.gnome.org/libsecret/) / [GNOME Keyring](https://gitlab.gnome.org/GNOME/gnome-keyring) | Secret storage | Upstream LGPL/GPL licenses |
| [Blur my Shell](https://github.com/aunetx/blur-my-shell) | Optional real background blur | GPL-3.0-or-later; not bundled |
| [KDE Connect](https://kdeconnect.kde.org/) | Optional file sharing with paired devices | GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL and per-file licenses; installed separately |
| [BlueZ](https://www.bluez.org/) / [UPower](https://upower.freedesktop.org/) | Bluetooth and system battery data | Upstream GPL/LGPL licenses; system services |
| [PulseAudio](https://www.freedesktop.org/wiki/Software/PulseAudio/), or [PipeWire](https://pipewire.org/) compatibility | Volume controls through `pactl` | System services, not bundled |
| [Python](https://www.python.org/), [X.Org](https://www.x.org/), [systemd](https://systemd.io/) | Runtime, X11 control and user services | Respective upstream licenses |
| [Noto CJK](https://github.com/notofonts/noto-cjk) | Recommended CJK-capable system font | SIL Open Font License |

Toss, Open-Meteo and Home Assistant HTTP endpoints are **external service integrations**, not bundled stock-data services. Public website presets are URLs, not copies of those applications. Chromium is an optional open-source browser; proprietary Google Chrome is an optional user-installed alternative. See [third-party notices](THIRD_PARTY_NOTICES.md) for provenance and license links.

This repository's original configuration, scripts, native patch and SVG artwork are available under the [MIT License](LICENSE). Upstream projects retain their own copyrights and licenses.

## Development checks

```bash
make test
make test-native
make test-stacks
make test-gestures  # Xvfb + Rust; builds the native smooth-scroll tests
```

See [validation scope](docs/VALIDATION.md) for the desktop checks actually performed. CI checks the package on Ubuntu 22.04 and 24.04. These checks cover blank defaults, installation under different user paths, configuration preservation, API adapters with mock data and source-patch applicability. They do not replace desktop testing on each GNOME release.
