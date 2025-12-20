# TvOverlay UI

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/manjotsc/ha-tvoverlay?style=flat-square)](https://github.com/manjotsc/ha-tvoverlay/releases)
[![License](https://img.shields.io/github/license/manjotsc/ha-tvoverlay?style=flat-square)](LICENSE)

A Home Assistant custom integration for [TvOverlay](https://github.com/gugutab/TvOverlay) - the Android TV overlay application by [@gugutab](https://github.com/gugutab).

Send notifications, display persistent widgets, and control overlay settings on your Android TV devices directly from Home Assistant.

---

## Credits

This integration is built for the **TvOverlay** Android TV application created by **[gugutab](https://github.com/gugutab)**.

- **Official TvOverlay App**: [github.com/gugutab/TvOverlay](https://github.com/gugutab/TvOverlay)
- **Download**: Available on [Google Play Store](https://play.google.com/store/apps/details?id=com.gugutab.tvoverlay)

Please support the original developer by starring the official repository and leaving a review on the Play Store!

---

## Features

### Services

| Service | Description |
|---------|-------------|
| `tvoverlay_ui.notify` | Send a notification to your TV |
| `tvoverlay_ui.notify_fixed` | Send a persistent/fixed notification widget |
| `tvoverlay_ui.clear_fixed` | Clear a specific fixed notification by ID |

### Entity Controls

| Entity Type | Entities | Description |
|-------------|----------|-------------|
| **Switch** | Display Clock | Toggle the clock overlay on/off |
| | Display Notifications | Toggle notification display |
| | Display Fixed Notifications | Toggle fixed notification display |
| | Pixel Shift | Enable anti-burn-in pixel shifting |
| | Debug Mode | Toggle debug overlay |
| **Number** | Clock Visibility | Adjust clock opacity (0-95%) |
| | Overlay Visibility | Adjust background overlay opacity (0-95%) |
| | Fixed Notifications Visibility | Adjust fixed notifications opacity (-1 to 95%) |
| | Notification Duration | Set default notification duration (1-60 seconds) |
| **Sensor** | Active Fixed Notifications | Shows IDs of active fixed notifications |

### Notification Features

**Standard Notifications (`tvoverlay_ui.notify`):**
- Title and message
- Small icon (MDI icons or image URL)
- Small icon color (hex or color name)
- Large icon (MDI icons or image URL)
- Media display (images or video streams)
- Screen corner positioning
- Custom duration

**Fixed Notifications (`tvoverlay_ui.notify_fixed`):**
- Persistent on-screen widgets
- Custom icons (MDI or image URL)
- Message text with custom color
- Icon color customization
- Border color
- Background color with opacity
- Shape options (circle, rounded, rectangular)
- Auto-expiration (e.g., "1h", "30m", "1h30m")

---

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select **Custom repositories**
4. Add repository URL: `https://github.com/manjotsc/ha-tvoverlay`
5. Select category: **Integration**
6. Click **Add**
7. Search for "TvOverlay UI" and click **Install**
8. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy the `custom_components/tvoverlay_ui` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

---

## Configuration

1. Go to **Settings** > **Devices & Services**
2. Click **+ Add Integration**
3. Search for "TvOverlay UI"
4. Enter your device details:
   - **Host**: IP address of your Android TV (e.g., `192.168.1.100`)
   - **Port**: TvOverlay port (default: `5001`)
   - **Device Name**: Friendly name for this device

---

## Limitations

### Media & Icons

- **Local paths are NOT supported** for images, videos, or icons
- All media URLs must be fully qualified (e.g., `http://192.168.1.100:8123/local/image.jpg`)
- The Android TV cannot access Home Assistant's local filesystem directly
- For local images, use Home Assistant's `/local/` folder and reference via full URL

### Video Formats

- **Supported**: RTSP streams, HLS (`.m3u8`), DASH (`.mpd`)
- **NOT Supported**: MP4 files, local video files
- Video must be a streaming URL accessible from your Android TV

### Fixed Notification Tracking

- The sensor only tracks fixed notifications created through Home Assistant
- Notifications created directly on the device or via other methods won't appear in the sensor
- There is no API to query existing notifications from the device

### General

- This integration uses a "fire and forget" approach - settings are sent but not polled back
- Entity states show assumed values and may not reflect actual device state if changed externally
- The TvOverlay app must be running on your Android TV for notifications to work

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Disclaimer

This is an unofficial community integration. It is not affiliated with, endorsed by, or connected to the official TvOverlay project or its developer.
