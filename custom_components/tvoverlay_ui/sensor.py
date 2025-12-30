"""Sensor platform for TvOverlay."""
from __future__ import annotations

import socket

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TvOverlay sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device_name = data["name"]

    sensors = [
        TvOverlayNotificationIdsSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            device_name=device_name,
            entry_data=data,
        ),
        TvOverlayHostnameSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            device_name=device_name,
        ),
        TvOverlayResolvedIpSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            device_name=device_name,
        ),
    ]

    async_add_entities(sensors)


class TvOverlayNotificationIdsSensor(SensorEntity):
    """Sensor showing active fixed notification IDs."""

    _attr_has_entity_name = True
    _attr_translation_key = "active_notification_ids"
    _attr_icon = "mdi:identifier"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator,
        entry_id: str,
        device_name: str,
        entry_data: dict,
    ) -> None:
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._entry_id = entry_id
        self._device_name = device_name
        self._entry_data = entry_data
        self._attr_unique_id = f"{entry_id}_active_notification_ids"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.device_identifier)},
            name=self._device_name,
            manufacturer="TvOverlay",
            model="Android TV Overlay",
            sw_version=self._coordinator.device_version,
            configuration_url=f"http://{self._coordinator.client.host}:{self._coordinator.client.port}",
        )

    @property
    def native_value(self) -> str:
        """Return the list of notification IDs as comma-separated string."""
        ids = self._entry_data.get("notification_ids", [])
        return ", ".join(ids) if ids else "None"

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        ids = self._entry_data.get("notification_ids", [])
        return {
            "notification_ids": ids,
            "count": len(ids),
        }

    async def async_added_to_hass(self) -> None:
        """Register update listener when entity is added."""
        self._entry_data["update_listeners"].append(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister update listener when entity is removed."""
        if self._handle_update in self._entry_data["update_listeners"]:
            self._entry_data["update_listeners"].remove(self._handle_update)

    @callback
    def _handle_update(self) -> None:
        """Handle notification ID list updates."""
        self.async_write_ha_state()


class TvOverlayHostnameSensor(SensorEntity):
    """Sensor showing device hostname."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:dns"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator,
        entry_id: str,
        device_name: str,
    ) -> None:
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._entry_id = entry_id
        self._device_name = device_name
        self._attr_unique_id = f"{entry_id}_hostname"
        self._attr_name = "Hostname"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.device_identifier)},
            name=self._device_name,
            manufacturer="TvOverlay",
            model="Android TV Overlay",
            sw_version=self._coordinator.device_version,
            configuration_url=f"http://{self._coordinator.client.host}:{self._coordinator.client.port}",
        )

    @property
    def native_value(self) -> str:
        """Return the hostname and port."""
        return f"{self._coordinator.client.host}:{self._coordinator.client.port}"


class TvOverlayResolvedIpSensor(SensorEntity):
    """Sensor showing resolved IP address."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:ip-network"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator,
        entry_id: str,
        device_name: str,
    ) -> None:
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._entry_id = entry_id
        self._device_name = device_name
        self._attr_unique_id = f"{entry_id}_ip_address"
        self._attr_name = "IP Address"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.device_identifier)},
            name=self._device_name,
            manufacturer="TvOverlay",
            model="Android TV Overlay",
            sw_version=self._coordinator.device_version,
            configuration_url=f"http://{self._coordinator.client.host}:{self._coordinator.client.port}",
        )

    @property
    def native_value(self) -> str:
        """Return the resolved IP address and port."""
        host = self._coordinator.client.host
        port = self._coordinator.client.port
        try:
            resolved_ip = socket.gethostbyname(host)
            return f"{resolved_ip}:{port}"
        except socket.gaierror:
            return f"{host}:{port}"
