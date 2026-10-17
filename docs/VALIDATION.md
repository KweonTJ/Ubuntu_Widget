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
- Ran 13 automated tests covering API adapters with mock credentials/data, failure handling, local usage opt-in, clean defaults, installation into different home directories (including spaces), upgrade preservation and Wayland rejection.
- Ran public-export checks for personalized defaults, credential patterns, machine-specific paths and accidentally included recordings or archives.

No real Toss/Home Assistant account credentials were used in these checks. A successful mock API test is not a verification of every provider's live account behavior.

The CI workflow runs package checks on Ubuntu 22.04 and 24.04. It does not launch a GNOME desktop, and its results must not be presented as full Ubuntu 24.04 desktop verification. That target remains experimental.
