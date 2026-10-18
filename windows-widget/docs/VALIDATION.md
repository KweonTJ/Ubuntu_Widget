# Windows edition validation

## Verified on the Ubuntu build host

- Node model/render tests: geometry clamping (including a monitor left of the primary), both-side resizing, minimum height, same-size/65% stack matching, merged-stack splitting across state reload, atomic state persistence/corrupt-file recovery, URL restrictions, escaping task/note text, completed task folding, album cover layout, battery identity, Sunday-first calendar and missing-provider states.
- Electron/Chromium UI smoke: renders all 36 library entries at 192 × 96, checks real IPC add/update/remove, stack merge/split, gallery/clock capture, dark/light appearance and minimum-size battery/music/screen-time captures. Uses a separate `.smoke-profile`; fixture hardware values in `*-minimum.png` are **test illustrations**, not readings from Windows hardware.
- Local UI smoke uses software rendering and `--no-sandbox` **only to run in the restricted Linux build sandbox**. This flag is not included in the Windows launcher, installer or CI workflow. Production renderer sandboxing, context isolation, disabled Node integration and CSP stay enabled.
- Windows x64 EXE/ZIP are cross-built with electron-builder and a custom native NSIS script (no Wine execution required). `scripts/check-package.cjs` checks packaged source matches the current source and rejects private profile/config paths; Electron/Chromium and systeminformation license files are retained.

- A live Open-Meteo geocoding/forecast probe from the restricted build host timed out; live weather connectivity was not validated here.

## Automated Windows checks

The repository's [Windows workflow](https://github.com/KweonTJ/Ubuntu_Widget/actions/workflows/windows.yml) runs on **Windows Server 2025**, not a physical Windows 11 PC. It checks:

- 15 Node model/render/installer tests, PowerShell syntax and a basic native adapter response.
- Isolated Electron rendering of all 36 entries, IPC add/update/remove and stack merge/split.
- Native Windows EXE/ZIP packaging and source/license/profile-exclusion checks.
- Silent per-user installation and removal, including preserving local user data and unrelated files in the destination.
- SHA-256 checksums and downloadable build artifacts.

The release notes link the successful run used for each release. These checks do not validate real Bluetooth devices, media players, account login or physical gestures.

## Not verified on Windows 11 hardware

The following require a Windows 11 PC; successful cross-compilation does not establish them:

- Installer first launch, taskbar pinning, tray, login startup and uninstall behavior.
- Acrylic appearance across Windows builds and DPI/multiple-monitor changes.
- Real mouse drag/edge resize and physical Precision Touchpad gestures.
- PC and Bluetooth battery devices, Windows PowerShell/WinRT media metadata, artwork and controls.
- Foreground app usage data and Windows notifications.
- Real todomate email/password login and today-task writes in the Electron session.
- Obsidian URI handling, KDE Connect transfers and Home Assistant authentication/control.

No connected accounts or devices were used on the build host. Linux Ubuntu Widget's live profile was not read or migrated. Windows CI results are recorded in the workflow linked above; they do not establish physical Windows 11 compatibility.

## Recheck on Windows

```powershell
npm ci
npm test
npm run smoke
powershell -NoProfile -File native/windows.ps1 -Action Snapshot
npm run build
node scripts/check-package.cjs
```

Use the EXE in a standard user account. Add two clocks, drag/resize from both sides and full bottom, create a same-size stack, switch it and restart. Connect optional services in the UI and confirm writes on the service's own screen. Verify theme, transparency and window placement on the intended Windows build. CI uses Windows Server 2025, not physical Windows 11 hardware.
