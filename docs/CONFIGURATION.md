# Configuration reference

Run `~/.local/bin/ubuntu-widget edit` to change normal settings. The UI is primarily Korean; README sections give the corresponding labels.

The default configuration directory is `~/.config/ubuntu-widget`, or `$XDG_CONFIG_HOME/ubuntu-widget` when set. Do not edit the clean templates inside this repository to store personal data.

| File | Purpose |
| --- | --- |
| `widget-settings.json` | Your note, tasks, countdown, focus timer, local events and optional world-clock list |
| `web-widgets.json` | Your named website URLs |
| `connections.json` | Non-secret settings: chosen symbols, coordinates, Home Assistant address/entity IDs, opt-in flags |
| `positions.json` | Automatically saved per-widget position and size |
| `hidden-widgets.json` / `enabled-widgets.json` | Visibility and added optional widgets |
| `theme-mode` | `auto`, `light` or `dark` |
| `glass-settings.json` | Global switch and per-widget overrides |
| `eww.scss` / `themes/dark.scss` | Source styles for light/dark cards |
| `appearance.scss` / `glass.scss` / `web-windows.yuck` | Generated files; avoid hand edits |

API keys and tokens are **not stored in these files**. They are in Secret Service. Even non-secret configuration can be private (for example, a server address or note), so keep it out of public repositories.

## World-clock cities

Stop the widgets before hand-editing JSON, preserve other keys in the file, and add this key to your installed `widget-settings.json`:

```json
{
  "worldclock": {
    "cities": [
      ["London", "Europe/London"],
      ["New York", "America/New_York"],
      ["Tokyo", "Asia/Tokyo"]
    ]
  }
}
```

Use valid [IANA timezone identifiers](https://www.iana.org/time-zones). World clocks account for daylight saving time. The digital/analog clock and upcoming local events follow your system timezone.

## Commands

```bash
ubuntu-widget edit
ubuntu-widget start
ubuntu-widget hide
ubuntu-widget toggle
ubuntu-widget restart
ubuntu-widget restore
ubuntu-widget theme auto
ubuntu-widget theme light
ubuntu-widget theme dark
ubuntu-widget reset
```

If `~/.local/bin` is not in your PATH, use the absolute launcher path. `reset` backs up the saved positions before returning to default placements. `restore` restores removed original widgets and optional widgets that were previously added; it does not open every optional library item.

## Developer overrides

- `EWW_WIDGET_CONFIG`: alternative installed configuration directory.
- `EWW_WIDGET_BINARY`: path to the patched Eww executable.
- `EWW_INTEGRATION_CACHE`: isolated integration cache directory.
- `EWW_WIDGET_APP_ID`: alternative GTK application ID for isolated development sessions.
- `EWW_GLASS_SKIP_COMPOSITOR=1`: render the glass palette without changing compositor preferences during development.

An override changes the Secret Service profile namespace. Reconnect accounts when moving to another configuration path. The source package intentionally uses a separate directory and application ID from any previous private Eww setup.
