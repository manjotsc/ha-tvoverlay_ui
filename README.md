<h1 align="center">
  <br>
  TvOverlay UI
  <br>
</h1>

<h4 align="center">A Home Assistant integration for <a href="https://github.com/gugutab/TvOverlay">TvOverlay</a> — send notifications and control overlays on your Android TV.</h4>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge" alt="HACS"></a>
  <a href="https://github.com/manjotsc/ha-tvoverlay_ui/releases"><img src="https://img.shields.io/github/v/release/manjotsc/ha-tvoverlay_ui?style=for-the-badge" alt="Release"></a>
  <a href="https://github.com/manjotsc/ha-tvoverlay_ui/stargazers"><img src="https://img.shields.io/github/stars/manjotsc/ha-tvoverlay_ui?style=for-the-badge" alt="Stars"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/manjotsc/ha-tvoverlay_ui?style=for-the-badge" alt="License"></a>
</p>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=manjotsc&repository=ha-tvoverlay_ui">
    <img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store." />
  </a>
</p>

<p align="center">
  <a href="#installation">Installation</a> &bull;
  <a href="#setup">Setup</a> &bull;
  <a href="#features">Features</a> &bull;
  <a href="#services">Services</a> &bull;
  <a href="#limitations">Limitations</a>
</p>

---

> [!NOTE]
> This integration is built for the [TvOverlay](https://github.com/gugutab/TvOverlay) Android TV app by [@gugutab](https://github.com/gugutab).

## Installation

### HACS (Recommended)

1. Open **HACS** → Search **TvOverlay UI**
2. Install → Restart Home Assistant

### Manual

Copy `custom_components/tvoverlay_ui` to your Home Assistant config directory and restart.

## Setup

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **TvOverlay UI**
3. Enter device IP, port (default: `5001`), and name
4. Optionally set a **Device Identifier** (e.g., `living_room_tv`) for stable automations

## Features

### Controls

| Type | Entities |
|:-----|:---------|
| **Switches** | Display Clock, Display Notifications, Display Fixed Notifications, Pixel Shift, Debug Mode |
| **Sliders** | Clock Visibility, Overlay Visibility, Fixed Notifications Visibility, Notification Duration |
| **Selects** | Hot Corner, Default Shape |
| **Sensors** | Active Fixed Notifications, Hostname, IP Address |
| **Binary Sensors** | Connectivity (online/offline status) |

### Stable Device Identifier

> [!TIP]
> **Prevent broken automations!** Set a **Device Identifier** (e.g., `living_room_tv`) during setup. This ID stays the same even if you delete and re-add the integration.

- Set during initial setup or via the **Configure** button
- Use lowercase letters, numbers, and underscores only
- Auto-generated from device name if left empty

## Services

| Service | Description |
|:--------|:------------|
| `tvoverlay_ui.notify` | Send a notification |
| `tvoverlay_ui.notify_fixed` | Create a persistent widget (ID required) |
| `tvoverlay_ui.clear_fixed` | Remove a widget by ID |

### Targeting Devices

| Field | Description | Recommended |
|:------|:------------|:-----------:|
| `target` | Stable device identifier | **Yes** |
| `device_id` | Dropdown selector | No (changes on re-add) |
| `host` | Manual `host:port` | For unconfigured devices |

<details>
<summary><strong>Example service call</strong></summary>

```yaml
service: tvoverlay_ui.notify
data:
  target: living_room_tv
  title: "Hello"
  message: "World"
```

</details>

## Limitations

> [!WARNING]
> Entity states are polled from the device every 30 seconds.

| Area | Limitation |
|:-----|:-----------|
| **Media** | Local paths not supported — use full URLs only |
| **Video** | Only RTSP, HLS (`.m3u8`), DASH (`.mpd`) — no MP4 |
| **Tracking** | Only tracks fixed notifications created via Home Assistant |

## Contributing

Pull requests are welcome! Feel free to open an [issue](https://github.com/manjotsc/ha-tvoverlay_ui/issues) for bugs or feature requests.

## License

[MIT](LICENSE)
