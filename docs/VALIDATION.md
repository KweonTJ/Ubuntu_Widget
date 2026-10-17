# Validation scope

Validated on 2026-10-17 using Ubuntu 22.04.5 LTS, GNOME 42 and a full Xorg session on x86-64.

- Built the pinned Eww source plus the native-control patch using stable Rust 1.99.0.
- Installed into an isolated, empty user profile using the public installer and freshly built executable.
- Loaded all 26 native window definitions and verified the 34-choice library (eight choices are website presets).
- Exercised mouse movement, 16 px snapping, two-dimensional resizing and upper-left removal on the installed native clock card.
- Opened weather, stocks, home, screen-time, agenda, analog-clock and podcast cards without supplying shared accounts or enabling tracking.
- Confirmed that the digital clock follows the test user's system timezone.
- Confirmed coexistence with an existing Eww setup without changing its window geometry.
- Checked the runtime log for configuration/Python errors.
- Ran 16 automated tests covering API adapters with mock credentials/data, failure handling, local usage opt-in, clean defaults, installation into different home directories (including spaces), upgrade preservation, first-run template synchronization and Wayland rejection.
- Ran public-export checks for personalized defaults, credential patterns, machine-specific paths and accidentally included recordings or archives.

No real Toss/Home Assistant account credentials were used in these checks. A successful mock API test is not a verification of every provider's live account behavior.

## Debian release checks (0.1.1)

- Built an amd64 `.deb` on Ubuntu 22.04, with shared-library minimums calculated by `dpkg-shlibdeps`.
- Installed it with APT in a separate Ubuntu 22.04 Docker environment and checked that installation creates no user configuration or autostart entries.
- Initialized two separate users, verified blank defaults, and preserved one user's note through a program-template update without affecting the other user.
- Rejected root and Wayland launches before initialization.
- Opened all 26 native widget windows and the GTK library under Xvfb. Verified world-clock and analog-clock data and checked their logs for errors. This revealed and fixed missing timezone data and an empty initial analog-image path.
- Purged the package and verified that its program files were removed while user content remained.
- Checked package ownership, paths and files for developer-home paths; remapped home, Cargo and generated-source paths out of the rebuilt engine.
- Resolved the source archive's locked Cargo graph offline using its vendored dependencies. Collected dependency/toolchain notices and supplied patched source with rebuild/relink instructions.

The container smoke test is reproducible with `make test-deb`. It uses a virtual X server, not GNOME, so it does not extend the desktop support claim or re-verify GNOME-specific blur/stacking behavior.

The CI workflow runs package checks on Ubuntu 22.04 and 24.04. It does not launch a GNOME desktop, and its results must not be presented as full Ubuntu 24.04 desktop verification. That target remains experimental.

## Body drag and two-sided width controls

A physical pointer test on an isolated Xvfb display verified label/body dragging,
dragging from inside a scroll viewport, 16 px movement, left-edge and right-edge
resizing, keeping the opposite edge fixed, the minimum width, normal button
clicks, ignoring drags on controls, scrolling, right-click handling, and restoring
saved geometry after reopening. Run `make test-native` after building the engine;
install `xvfb` and `xauth` first. The ordinary test suite skips this optional GUI
test unless `EWW_NATIVE_TEST_BINARY` is provided.
