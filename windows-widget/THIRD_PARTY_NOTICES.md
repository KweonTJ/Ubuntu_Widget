# Third-party notices

This independent Windows edition derives its clean assets and todomate compatibility adapter from Ubuntu Widget (MIT). Eww and GTK are **not bundled or used** by the Windows renderer. No user configuration or credentials are included.

| Component | Purpose | License / upstream |
| --- | --- | --- |
| Electron 44.9.0 (Chromium, Node.js) | Windowing, sandboxed renderer, system theme, Windows Acrylic | MIT; bundled Chromium/Node notices included by Electron. https://github.com/electron/electron |
| systeminformation 5.33.15 | CPU, memory, disk, network and PC battery | MIT. https://github.com/sebhildebrandt/systeminformation |
| electron-builder 26.15.3 / NSIS | Build-time EXE and ZIP packaging | MIT / zlib-libpng. https://github.com/electron-userland/electron-builder / https://nsis.sourceforge.io/License |
| Ubuntu Widget | Original SVG assets and todomate compatibility adapter | MIT. https://github.com/KweonTJ/Ubuntu_Widget |
| Open-Meteo | Optional city search and weather forecast service | Weather data: CC BY 4.0; service terms apply. https://open-meteo.com/en/terms |

Optional user-installed services/apps (todomate, Obsidian, KDE Connect, Home Assistant, Toss Securities, websites) are not redistributed. Their terms and licenses apply. Apple icons, branding, macOS code and iPhone continuity services are not included. Typography uses the user's installed system fonts.

The npm lockfile pins transitive dependencies. Electron's `LICENSE.electron.txt` and `LICENSES.chromium.html` are included in the packaged runtime. Build dependencies remain outside the distributed app.
