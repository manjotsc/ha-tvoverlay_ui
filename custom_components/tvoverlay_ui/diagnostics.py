"""Diagnostics support for TvOverlay."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    # Get coordinator data
    coordinator_data = coordinator.data or {}

    return {
        "config_entry": {
            "entry_id": entry.entry_id,
            "title": entry.title,
            "host": entry.data.get(CONF_HOST),
            "port": entry.data.get(CONF_PORT),
        },
        "device": {
            "available": coordinator.available,
            "version": coordinator.device_version,
        },
        "state": {
            "overlay": coordinator_data.get("overlay", {}),
            "notifications": coordinator_data.get("notifications", {}),
            "settings": coordinator_data.get("settings", {}),
        },
        "active_notification_ids": data.get("notification_ids", []),
        "local_settings": {
            "hot_corner": data.get("hot_corner"),
            "default_shape": data.get("default_shape"),
        },
    }
