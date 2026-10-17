# Packaging and release maintenance

The `.deb` is an amd64 package built on Ubuntu 22.04. The verified desktop target
is GNOME 42 on Xorg. Ubuntu 24.04 remains experimental; Wayland is unsupported.

## Edit and rebuild

Keep a local clone in a directory named `ubuntu-widget`, wherever you prefer.
The Git checkout is the editable distribution source, not a backup of a live
user's configuration.

| Path | Edit here to change |
| --- | --- |
| `config/eww.yuck`, `config/eww.scss`, `config/themes/` | Widget layout, shared sizing and appearance |
| `config/scripts/` | Widget library, data adapters and behavior |
| `packaging/` | System launcher and application-menu entry |
| `scripts/initialize.py` | First-run configuration and upgrade preservation |
| `scripts/build-deb.py` | Debian package files and runtime dependencies |
| `patches/eww-native-controls.patch` | Native Eww movement and resizing |
| `VERSION` | Application version; increment before publishing changed release assets |
| `dist/` | Generated `.deb`, source archive and checksums; ignored by Git |

Install the source-build dependencies listed in the README, plus the package
tools below. Install stable Rust using rustup and authenticate `gh` if needed.
`gh` reads missing upstream license notices through GitHub's API; its login is
not copied into the output.

```bash
sudo apt install dpkg-dev binutils gh make
make test
make deb
make test-deb
```

`make deb` builds the patched engine, vendors its locked dependency source,
collects license notices, creates the `.deb`, and generates `dist/SHA256SUMS`.
Build on Ubuntu 22.04 amd64 to retain that release's library baseline. A build
on a newer distribution can raise the minimum shared-library requirements.
The builder uses `dpkg-shlibdeps` to calculate the actual ELF requirements.

`make test-deb` requires Docker and a running Docker daemon. It installs the
package in a disposable Ubuntu 22.04 container, checks two users and preservation
through a template update/purge, and opens the native widgets and GTK gallery
under Xvfb. It does not install the package on your own desktop or replace a
full GNOME session test.

To package an existing engine built by the current `build-eww.sh`:

```bash
make source
/usr/bin/python3 scripts/build-deb.py
cd dist
sha256sum *.deb *-source.tar.xz > SHA256SUMS
```

Use `--revision 2` (then 3, etc.) for a packaging-only revision of the same
application version. Never replace a published package with different contents
under the same version. Test the package before creating its GitHub release.

## What installation does

- APT installs the engine in `/usr/lib/ubuntu-widget/eww`, immutable templates
  in `/usr/share/ubuntu-widget/`, and a launcher in `/usr/bin/ubuntu-widget`.
- There are no root maintainer scripts, automatic downloads, user-home writes,
  account setup or autostart changes during package installation.
- The first non-root Xorg launch initializes
  `${XDG_CONFIG_HOME:-~/.config}/ubuntu-widget/` with blank defaults.
- Later template updates preserve the state-file list in `initialize.py`:
  notes/tasks/events, account configuration, websites, enabled/hidden widgets,
  positions, themes and glass settings. Keyring credentials are not copied.
- Initialization is serialized; individual program files are replaced
  atomically. An unrelated, unrecognized configuration directory is refused.
- Custom program/style edits in the runtime configuration survive ordinary
  launches but are replaced by a template update. Keep changes in the source
  checkout and rebuild the package to distribute them.
- Package removal and purge leave user configuration, cache and keyring data
  untouched. Stop widgets, disconnect accounts and disable glass first.

An older per-user source launcher in `~/.local/bin` can take precedence in the
terminal. Uninstall the source installation before switching; its uninstall
keeps saved configuration. The system desktop entry always uses `/usr/bin`.

## Release assets

Publish the `.deb`, `SHA256SUMS`, and the matching `*-source.tar.xz` together.
The latter includes the complete patched engine and vendored Cargo sources,
including LGPL Rust libraries and the application source needed to relink them.
Its `BUILD.md` explains offline rebuilding and selecting a modified engine.
The ordinary GitHub auto-generated source archive alone is not a replacement.

No personal configuration, browser data, API keys, recordings, local paths or
desktop backups should be included. Run `scripts/check_public.py` before every
release. The package builder also rejects home-directory paths embedded in
the engine, which are remapped by the engine build script.
