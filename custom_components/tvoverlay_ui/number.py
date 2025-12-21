"""Number platform for TvOverlay."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import TvOverlayEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class TvOverlayNumberEntityDescription(NumberEntityDescription):
    """Describes TvOverlay number entity."""

    api_key: str
    endpoint: str  # "notifications" or "overlay"
    data_key: str  # Key in coordinator data


NUMBER_DESCRIPTIONS: tuple[TvOverlayNumberEntityDescription, ...] = (
    TvOverlayNumberEntityDescription(
        key="clock_visibility",
        translation_key="clock_visibility",
        icon="mdi:clock-outline",
        native_min_value=0,
        native_max_value=95,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        api_key="clockOverlayVisibility",
        endpoint="overlay",
        data_key="overlay",
    ),
    TvOverlayNumberEntityDescription(
        key="overlay_visibility",
        translation_key="overlay_visibility",
        icon="mdi:opacity",
        native_min_value=0,
        native_max_value=95,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        api_key="overlayVisibility",
        endpoint="overlay",
        data_key="overlay",
    ),
    TvOverlayNumberEntityDescription(
        key="fixed_notifications_visibility",
        translation_key="fixed_notifications_visibility",
        icon="mdi:pin-outline",
        native_min_value=-1,
        native_max_value=95,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        api_key="fixedNotificationsVisibility",
        endpoint="notifications",
        data_key="notifications",
    ),
    TvOverlayNumberEntityDescription(
        key="notification_duration",
        translation_key="notification_duration",
        icon="mdi:timer-outline",
        native_min_value=1,
        native_max_value=60,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        api_key="notificationDuration",
        endpoint="notifications",
        data_key="notifications",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TvOverlay number entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device_name = data["name"]

    entities = [
        TvOverlayNumber(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            device_name=device_name,
            description=description,
            client=data["client"],
        )
        for description in NUMBER_DESCRIPTIONS
    ]

    async_add_entities(entities)


class TvOverlayNumber(TvOverlayEntity, NumberEntity):
    """Representation of a TvOverlay number entity."""

    entity_description: TvOverlayNumberEntityDescription

    def __init__(
        self,
        coordinator,
        entry_id: str,
        device_name: str,
        description: TvOverlayNumberEntityDescription,
        client,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, entry_id, device_name)
        self.entity_description = description
        self._client = client
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.coordinator.data is None:
            return None
        data_section = self.coordinator.data.get(self.entity_description.data_key, {})
        value = data_section.get(self.entity_description.api_key)
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        int_value = int(value)
        data = {self.entity_description.api_key: int_value}

        if self.entity_description.endpoint == "notifications":
            success = await self._client.set_notifications(data)
        else:  # overlay
            success = await self._client.set_overlay(data)

        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(
                "Failed to set %s to %s",
                self.entity_description.key,
                value,
            )
