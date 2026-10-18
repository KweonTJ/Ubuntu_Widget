# Validation scope

## Version 2.1 (2026-10-18)

- Automatic stack creation was exercised with real XTest pointer drags on isolated Xvfb displays at both 1x and 2x scale. The same test checks subsequent dragging, resizing, page-counter clicks/wheel input, reopening and splitting back to original placements.
- Unit checks cover the 65% equal-size overlap rule, stale/mismatched/hidden targets, merging existing stacks while retaining original placements, and rollback after an engine failure.
- Three native Rust tests cover continuous horizontal scroll accumulation, one switch per stroke including inertia after the next card maps, vertical/diagonal/noise rejection, and real queued GDK scroll dispatch through GTK. A vertical scroll viewport still moves, and reactive enabling/disabling of stack gestures is checked.
- The host touchpad has two-finger and horizontal scrolling enabled. Tests inject continuous GDK events; they do not claim a physical finger swipe on the user's touchpad.
- `make test` passes 31 checks and skips two opt-in GUI tests. Native pointer, embedded WebKit and automatic-stack GUI tests pass separately.
- The 2.1 Debian package passed installation, two-user initialization, program-template update with content preservation, all 27 native cards and the GTK library on Xvfb, and purge with user data retained in a clean Ubuntu 22.04 container.
- Ubuntu support boundaries remain unchanged: full desktop verification is Ubuntu 22.04.5 / GNOME 42 / Xorg / amd64. Other releases and Wayland gain no new support claim.

## Version 2.0 (2026-10-18)

- Ubuntu 22.04.5 LTS / GNOME 42 / Xorg / amd64 remains the desktop-verified environment.
- Unit checks cover providers, per-user installation, Obsidian reads/vault boundaries, responsive metrics, and KDE Connect filtering/multi-file requests.
- Xvfb sessions rendered the native catalogue in light/dark modes, representative compact/expanded cards, and both library themes.
- Physical pointer tests verified body dragging, both resize edges, ordinary controls, saved positions, and a local embedded WebKit page's checkbox. No account data was used by these tests.
- The desktop update preserves provider settings, personal content, layout and the existing todomate login profile. Obsidian connected to a registered local vault.
- A real local todomate session loaded today's task list. A temporary connector test task was checked and unchecked through the same command path used by the native widget, then removed. No existing personal task was modified. This validates this account/session, not every possible account or future provider schema.
- The page-adapter contract test covers ownership/date checks, stale completion conflicts, active timers and logout. Stale/previous-day local snapshots are rejected.
- Stack checks cover equal-size selection, page switching, common movement/size, restart, split, removal and failed-switch rollback. `make test-stacks` uses physical mouse clicks, wheel events, body dragging and edge resizing on Xvfb.
- `make test` passes 27 checks and skips the two opt-in GUI tests; `make test-native`, `make test-webview` and the stack GUI test pass separately. All 27 native cards render in light/dark modes without engine errors.
- The 2.0 Debian package installed, initialized two users, rendered all 27 native cards and the GTK library, preserved content through a template update, and purged its program files while retaining user data in a clean Ubuntu 22.04 container.
- Ubuntu 24.04 remains experimental; no new full-desktop support claim is made for other releases or Wayland.

## Earlier validation

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

The pointer test also passed at 2x scale on Xvfb with a 2560 × 2048 virtual
screen (`EWW_NATIVE_TEST_SCALE=2`). On the GNOME/Xorg desktop with glass enabled,
body dragging and both edge controls were exercised on an installed card and
its layout was restored. The glass frame inset now matches the 8 px canvas
padding so Mutter does not discard clicks on the card edges; resize targets
are 16 logical pixels wide.
