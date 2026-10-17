# Privacy and clean distribution

## What is shipped

Only source code, original SVG assets, neutral default settings, documentation and the native Eww patch are published. The release templates start with:

- no visible/added desktop cards;
- no saved window positions, notes, tasks, events, websites, watchlists or Home Assistant entities;
- no city/coordinates and no provider connection;
- screen-time recording and glass effects disabled;
- system-local clock timezone instead of a developer's fixed location.

No personal desktop backup, executable built on a developer's machine, browser session, recorded desktop video, device battery snapshot, log or keyring export is included. A documentation preview, when present, is rendered using clean defaults and illustrative card values only.

## What happens on your machine

- Notes, events, positions, website URLs and non-secret provider settings remain in your user configuration directory.
- API credentials are stored in GNOME Keyring via libsecret. The app does not offer a plaintext fallback and never asks you to paste credentials into an issue or chat.
- Provider failures are displayed without returning raw credential-bearing response bodies or request URLs to the UI.
- Weather requests send the search text/coordinates you choose to Open-Meteo.
- Stocks requests go to the fixed Toss Securities API host. Only authentication and read-only market-data endpoints are used.
- Home requests go to your configured server. A device command is sent only when you click a registered light/switch control.
- Website launchers delegate to your browser; the app does not inspect browser cookies.
- Screen time is off until you opt in. When enabled and a desktop card is open, local application identity and sampled duration are stored; window titles, document names and URLs are not recorded. You can stop or clear collection in the app.
- There is no analytics or telemetry service.

Runtime settings are not safe to publish merely because they do not contain an API secret. Server URLs, coordinates, notes, events and app history can all identify a person. Do not copy your live configuration into this Git checkout. `scripts/check_public.py` rejects personalized defaults and common secret patterns before the initial publication and in CI.

## Removing data

Disconnect each provider in the app to remove this application's saved keyring entry. Revoke the provider-side credential separately if desired. Turn glass effects off to restore this integration's saved compositor settings before uninstalling. The uninstaller preserves user configuration and cache so that reinstalling does not erase notes or other content; erase those directories yourself only when intended.
