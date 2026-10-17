# Third-party notices

## Distributed upstream material

- **Eww**, by ElKowar and contributors: https://github.com/elkowar/eww
- The native-controls patch targets commit `48f5aa8b379adf29da0b0bb9ca04164f65d8bdaa` (Eww 0.6.0).
- Eww uses the **MIT License**. Its copyright and permission text are retained in [`LICENSES/Eww-MIT.txt`](LICENSES/Eww-MIT.txt).
- `patches/eww-native-controls.patch` adds grid movement, persisted placement and resize support, and adjusts the native widget definitions and their lifecycle. The rest of Eww is fetched at build time, not copied into this repository.
- Eww's Cargo dependencies and their licenses are described by the pinned source's `Cargo.lock` and individual packages. The Git repository does not vendor or relicense those dependencies.
- Release `.deb` files contain a compiled patched Eww engine, including statically linked Rust dependencies. Their individual notices and an inventory are installed under `/usr/share/doc/ubuntu-widget/rust-licenses/`. The matching release `*-source.tar.xz` contains the application, patched Eww and vendored dependency sources, with offline rebuild/relink instructions in `BUILD.md`.
- The Rust dbusmenu bindings are LGPL-3.0-only. Their corresponding source and the application source needed to rebuild/relink them are supplied in that accompanying source archive. Modified engines may be selected with `EWW_WIDGET_BINARY`; no signing key or device authorization is required. Reverse engineering for debugging modifications to those libraries is not restricted by this project. The LGPL and GPL texts accompany their notices.

## System dependencies and optional software

These projects run on the user's system and are not redistributed by this source package. Their licenses continue to apply:

- GTK/GLib: https://gitlab.gnome.org/GNOME/gtk and https://gitlab.gnome.org/GNOME/glib
- PyGObject: https://gitlab.gnome.org/GNOME/pygobject (LGPL-2.1-or-later)
- Cairo: https://www.cairographics.org/ and Pycairo: https://github.com/pygobject/pycairo (upstream LGPL/MPL alternatives)
- D-Bus: https://dbus.freedesktop.org/ and dbus-python: https://gitlab.freedesktop.org/dbus/dbus-python (see upstream `COPYING` for the library and bundled components)
- libsecret: https://gitlab.gnome.org/GNOME/libsecret and GNOME Keyring: https://gitlab.gnome.org/GNOME/gnome-keyring
- Blur my Shell: https://github.com/aunetx/blur-my-shell ([GPL-3.0-or-later license](https://github.com/aunetx/blur-my-shell/blob/master/LICENSE)); optional, not bundled
- BlueZ: https://github.com/bluez/bluez and UPower: https://gitlab.freedesktop.org/upower/upower
- PulseAudio: https://gitlab.freedesktop.org/pulseaudio/pulseaudio and PipeWire: https://gitlab.freedesktop.org/pipewire/pipewire
- X.Org Xlib and XScreenSaver: https://www.x.org/
- Python: https://docs.python.org/3/license.html
- systemd: https://github.com/systemd/systemd
- Noto CJK: https://github.com/notofonts/noto-cjk (SIL Open Font License; installed separately)

## External data and websites

- Weather: Open-Meteo, https://open-meteo.com/ (CC BY 4.0 data attribution; hosted API terms apply).
- Air quality: CAMS / Open-Meteo, https://open-meteo.com/en/docs/air-quality-api (follow the linked attribution requirements).
- Securities: Toss Securities Open API, https://developers.tossinvest.com/docs (the user supplies their own credentials; provider terms apply).
- Smart home: Home Assistant REST API, https://developers.home-assistant.io/docs/api/rest/ (user-owned server and token).
- Website presets link to third-party websites. None of their code, logos, cookies or signed-in content is bundled.

The project's SVG artwork is original project material under the repository's MIT License. No macOS/Apple artwork, wallpaper, system font, icon pack or binary is redistributed. Product names are used to identify integrations and compatibility only.
