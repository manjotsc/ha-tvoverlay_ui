"""The TvOverlay integration."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store

from .api import TvOverlayApiClient
from .const import (
    ATTR_BACKGROUND_COLOR,
    ATTR_BACKGROUND_OPACITY,
    ATTR_BORDER_COLOR,
    ATTR_CORNER,
    ATTR_DEVICE_ID,
    ATTR_DURATION,
    ATTR_EXPIRATION,
    ATTR_HOST,
    ATTR_ICON,
    ATTR_ICON_COLOR,
    ATTR_ID,
    ATTR_LARGE_ICON,
    ATTR_MEDIA_TYPE,
    ATTR_MEDIA_URL,
    ATTR_MESSAGE,
    ATTR_MESSAGE_COLOR,
    ATTR_SHAPE,
    ATTR_SMALL_ICON,
    ATTR_SMALL_ICON_COLOR,
    ATTR_SOURCE,
    ATTR_TARGET,
    ATTR_TITLE,
    ATTR_VISIBLE,
    CONF_DEVICE_IDENTIFIER,
    DEFAULT_PORT,
    DOMAIN,
    PLATFORMS,
    SERVICE_CLEAR_FIXED,
    SERVICE_NOTIFY,
    SERVICE_NOTIFY_FIXED,
    STORAGE_KEY,
    STORAGE_VERSION,
    VALID_CORNERS,
    VALID_SHAPES,
)
from .coordinator import TvOverlayCoordinator

_LOGGER = logging.getLogger(__name__)

# Hex color validation pattern
HEX_COLOR_PATTERN = re.compile(r"^#?[0-9A-Fa-f]{6}$")

# Common color names to hex mapping
COLOR_NAMES: dict[str, str] = {
    "red": "#FF0000",
    "green": "#00FF00",
    "blue": "#0000FF",
    "white": "#FFFFFF",
    "black": "#000000",
    "yellow": "#FFFF00",
    "orange": "#FFA500",
    "purple": "#800080",
    "pink": "#FFC0CB",
    "cyan": "#00FFFF",
    "magenta": "#FF00FF",
    "gray": "#808080",
    "grey": "#808080",
    "brown": "#A52A2A",
    "lime": "#00FF00",
    "navy": "#000080",
    "teal": "#008080",
    "maroon": "#800000",
    "olive": "#808000",
    "silver": "#C0C0C0",
    "aqua": "#00FFFF",
    "gold": "#FFD700",
    "coral": "#FF7F50",
    "salmon": "#FA8072",
    "violet": "#EE82EE",
    "indigo": "#4B0082",
    "turquoise": "#40E0D0",
}

# Default opacity for background colors
DEFAULT_OPACITY = 40

# Valid URL schemes for media URLs (including RTSP for camera streams)
VALID_MEDIA_URL_SCHEMES = {"http", "https", "rtsp", "rtsps"}


def media_url(value: Any) -> str:
    """Validate a media URL (supports http, https, rtsp, rtsps schemes)."""
    if value is None:
        raise vol.Invalid("URL cannot be None")
    url_str = str(value).strip()
    if not url_str:
        raise vol.Invalid("URL cannot be empty")
    parsed = urlparse(url_str)
    if parsed.scheme not in VALID_MEDIA_URL_SCHEMES:
        raise vol.Invalid(
            f"Invalid URL scheme '{parsed.scheme}'. "
            f"Supported schemes: {', '.join(sorted(VALID_MEDIA_URL_SCHEMES))}"
        )
    if not parsed.netloc:
        raise vol.Invalid("URL must have a valid host")
    return url_str


def _normalize_hex_color(color: str | None) -> str | None:
    """Normalize color to hex string (accepts hex or color names)."""
    if not color:
        return None
    color = color.strip().lower()
    # Check if it's a color name
    if color in COLOR_NAMES:
        return COLOR_NAMES[color]
    # Handle hex format
    if not color.startswith("#"):
        color = f"#{color}"
    # Validate hex format
    if HEX_COLOR_PATTERN.match(color):
        return color.upper()
    return None


def _hex_with_alpha(color: str | None, opacity: int | None) -> str | None:
    """Add alpha channel to hex color string (#RRGGBB -> #AARRGGBB)."""
    color = _normalize_hex_color(color)
    if color is None:
        return None
    # Remove # prefix, get RGB part
    rgb = color.lstrip("#")
    if len(rgb) == 6:
        # Convert opacity 0-100 to alpha 0-255
        alpha = int((opacity if opacity is not None else DEFAULT_OPACITY) * 255 / 100)
        return f"#{alpha:02X}{rgb}"
    return color


def _exactly_one_device_target(config: dict) -> dict:
    """Validate that exactly one of device_id, target, or host is provided."""
    device_id = config.get(ATTR_DEVICE_ID)
    target = config.get(ATTR_TARGET)
    host = config.get(ATTR_HOST)

    # Count how many are provided (non-empty)
    provided = sum(1 for v in [device_id, target, host] if v)

    if provided == 0:
        raise vol.Invalid(
            "You must provide exactly one of: Device (Dropdown), Device Identifier, or Host"
        )
    if provided > 1:
        raise vol.Invalid(
            "Please use only one of: Device (Dropdown), Device Identifier, or Host. "
            "Do not fill multiple fields."
        )
    return config


# Backward compatibility: map old camelCase field names to new snake_case
CAMEL_TO_SNAKE_MAP: dict[str, str] = {
    "smallIcon": ATTR_SMALL_ICON,
    "smallIconColor": ATTR_SMALL_ICON_COLOR,
    "largeIcon": ATTR_LARGE_ICON,
    "mediaType": ATTR_MEDIA_TYPE,
    "mediaUrl": ATTR_MEDIA_URL,
    "iconColor": ATTR_ICON_COLOR,
    "messageColor": ATTR_MESSAGE_COLOR,
    "borderColor": ATTR_BORDER_COLOR,
    "backgroundColor": ATTR_BACKGROUND_COLOR,
    "backgroundOpacity": ATTR_BACKGROUND_OPACITY,
}


def _normalize_service_data(config: dict) -> dict:
    """Normalize camelCase field names to snake_case for backward compatibility."""
    normalized = dict(config)
    for camel, snake in CAMEL_TO_SNAKE_MAP.items():
        if camel in normalized:
            # Only copy if snake_case version isn't already set
            if snake not in normalized:
                normalized[snake] = normalized[camel]
            del normalized[camel]
    return normalized


# Service schemas - exactly one of device_id, target, or host required
# Accepts both snake_case (new) and camelCase (legacy) field names for backward compatibility
NOTIFY_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Optional(ATTR_DEVICE_ID): cv.string,
            vol.Optional(ATTR_TARGET): cv.string,
            vol.Optional(ATTR_HOST): cv.string,
            vol.Optional(ATTR_ID): cv.string,
            vol.Optional(ATTR_TITLE): cv.string,
            vol.Optional(ATTR_MESSAGE): cv.string,
            vol.Optional(ATTR_SOURCE): cv.string,
            # New snake_case field names
            vol.Optional(ATTR_SMALL_ICON): cv.string,
            vol.Optional(ATTR_SMALL_ICON_COLOR): cv.string,
            vol.Optional(ATTR_LARGE_ICON): cv.string,
            vol.Optional(ATTR_MEDIA_TYPE): vol.In(["none", "image", "video"]),
            vol.Optional(ATTR_MEDIA_URL): media_url,
            # Legacy camelCase field names (backward compatibility)
            vol.Optional("smallIcon"): cv.string,
            vol.Optional("smallIconColor"): cv.string,
            vol.Optional("largeIcon"): cv.string,
            vol.Optional("mediaType"): vol.In(["none", "image", "video"]),
            vol.Optional("mediaUrl"): media_url,
            vol.Optional(ATTR_CORNER): vol.In(VALID_CORNERS),
            vol.Optional(ATTR_DURATION): cv.positive_int,
        },
        _normalize_service_data,
        _exactly_one_device_target,
    )
)

NOTIFY_FIXED_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Optional(ATTR_DEVICE_ID): cv.string,
            vol.Optional(ATTR_TARGET): cv.string,
            vol.Optional(ATTR_HOST): cv.string,
            vol.Optional(ATTR_ID): cv.string,
            vol.Optional(ATTR_VISIBLE, default=True): cv.boolean,
            vol.Optional(ATTR_ICON): cv.string,
            vol.Optional(ATTR_MESSAGE): cv.string,
            # New snake_case field names
            vol.Optional(ATTR_MESSAGE_COLOR): cv.string,
            vol.Optional(ATTR_ICON_COLOR): cv.string,
            vol.Optional(ATTR_BORDER_COLOR): cv.string,
            vol.Optional(ATTR_BACKGROUND_COLOR): cv.string,
            vol.Optional(ATTR_BACKGROUND_OPACITY): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            ),
            # Legacy camelCase field names (backward compatibility)
            vol.Optional("messageColor"): cv.string,
            vol.Optional("iconColor"): cv.string,
            vol.Optional("borderColor"): cv.string,
            vol.Optional("backgroundColor"): cv.string,
            vol.Optional("backgroundOpacity"): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            ),
            vol.Optional(ATTR_SHAPE): vol.In(VALID_SHAPES),
            vol.Optional(ATTR_EXPIRATION): cv.string,
        },
        _normalize_service_data,
        _exactly_one_device_target,
    )
)

CLEAR_FIXED_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Optional(ATTR_DEVICE_ID): cv.string,
            vol.Optional(ATTR_TARGET): cv.string,
            vol.Optional(ATTR_HOST): cv.string,
            vol.Required(ATTR_ID): cv.string,
        },
        _exactly_one_device_target,
    )
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TvOverlay from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    name = entry.data.get(CONF_NAME, host)
    # Get device identifier (default to host:port for stable device_id)
    device_identifier = entry.data.get(CONF_DEVICE_IDENTIFIER, f"{host}:{port}")

    session = async_get_clientsession(hass)
    client = TvOverlayApiClient(host, port, session)

    # Create coordinator
    coordinator = TvOverlayCoordinator(hass, client, name, device_identifier)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Initialize storage for notification IDs with lock
    store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")
    stored_data = await store.async_load()
    notification_ids: list[str] = []
    if stored_data and isinstance(stored_data.get("ids"), list):
        notification_ids = stored_data["ids"]

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "name": name,
        "host": host,
        "port": port,
        "device_identifier": device_identifier,
        "store": store,
        "storage_lock": asyncio.Lock(),
        "notification_ids": notification_ids,
        "update_listeners": [],
        "hot_corner": "top_start",
        "default_shape": "rounded",
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services if not already registered
    if not hass.services.has_service(DOMAIN, SERVICE_NOTIFY):
        await _async_register_services(hass)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

        # Unregister services if no more entries
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_NOTIFY)
            hass.services.async_remove(DOMAIN, SERVICE_NOTIFY_FIXED)
            hass.services.async_remove(DOMAIN, SERVICE_CLEAR_FIXED)

    return unload_ok


def _parse_host_port(host_string: str) -> tuple[str, int]:
    """Parse host:port string into host and port."""
    if ":" in host_string:
        parts = host_string.rsplit(":", 1)
        try:
            return parts[0], int(parts[1])
        except ValueError:
            return host_string, DEFAULT_PORT
    return host_string, DEFAULT_PORT


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register TvOverlay services."""

    def _get_client_from_device_id(device_id: str) -> TvOverlayApiClient | None:
        """Get the API client from a device registry ID."""
        device_registry = dr.async_get(hass)
        device = device_registry.async_get(device_id)

        if device is None:
            return None

        # Find the config entry for this device by matching device_identifier
        for identifier in device.identifiers:
            if identifier[0] == DOMAIN:
                device_identifier = identifier[1]
                # Search through all entries to find matching device_identifier
                for entry_data in hass.data[DOMAIN].values():
                    if isinstance(entry_data, dict):
                        if entry_data.get("device_identifier") == device_identifier:
                            return entry_data["client"]

        return None

    def _get_client_from_name_or_host(name_or_host: str) -> TvOverlayApiClient | None:
        """Get the API client by name or host."""
        for entry_data in hass.data[DOMAIN].values():
            if isinstance(entry_data, dict):
                if entry_data.get("name") == name_or_host or entry_data.get("host") == name_or_host:
                    return entry_data["client"]
        return None

    def _get_client_from_device_identifier(identifier: str) -> TvOverlayApiClient | None:
        """Get the API client by device_identifier."""
        for entry_data in hass.data[DOMAIN].values():
            if isinstance(entry_data, dict):
                if entry_data.get("device_identifier") == identifier:
                    return entry_data["client"]
        return None

    def _get_client(call_data: dict[str, Any]) -> TvOverlayApiClient:
        """Get the API client from service call data."""
        target = call_data.get(ATTR_TARGET)
        device_id = call_data.get(ATTR_DEVICE_ID)
        host = call_data.get(ATTR_HOST)

        # Try target first (stable device_identifier - recommended)
        if target:
            client = _get_client_from_device_identifier(target)
            if client:
                return client

        # Try device_id (from device selector dropdown)
        if device_id:
            # Try as device registry ID
            client = _get_client_from_device_id(device_id)
            if client:
                return client

            # Try as our stable device_identifier (fallback)
            client = _get_client_from_device_identifier(device_id)
            if client:
                return client

            # Try as name or host string
            client = _get_client_from_name_or_host(device_id)
            if client:
                return client

        # Try manual host:port
        if host:
            # Check if it matches a configured device
            parsed_host, parsed_port = _parse_host_port(host)
            for entry_data in hass.data[DOMAIN].values():
                if isinstance(entry_data, dict):
                    if entry_data.get("host") == parsed_host and entry_data.get("port") == parsed_port:
                        return entry_data["client"]

            # Create a new client for unconfigured device
            session = async_get_clientsession(hass)
            return TvOverlayApiClient(parsed_host, parsed_port, session)

        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="device_not_found",
        )

    def _get_entry_data_from_client(client: TvOverlayApiClient) -> dict[str, Any] | None:
        """Get the entry data for a client."""
        for entry_data in hass.data[DOMAIN].values():
            if isinstance(entry_data, dict) and entry_data.get("client") is client:
                return entry_data
        return None

    async def async_notify(call: ServiceCall) -> None:
        """Send a notification."""
        client = _get_client(call.data)
        entry_data = _get_entry_data_from_client(client)
        defaults = {
            "hot_corner": entry_data.get("hot_corner", "top_start") if entry_data else "top_start",
        }
        data = _build_notification_data(call.data, defaults)
        success = await client.send_notification(data)
        if not success:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="notification_failed",
            )

    async def _add_notification_id(entry_data: dict[str, Any], notification_id: str) -> None:
        """Add a notification ID to storage and notify listeners."""
        async with entry_data["storage_lock"]:
            ids = entry_data["notification_ids"]
            if notification_id not in ids:
                ids.append(notification_id)
                await entry_data["store"].async_save({"ids": ids})
        # Notify listeners (sensors) of the update
        for listener in entry_data["update_listeners"]:
            listener()

    async def _remove_notification_id(entry_data: dict[str, Any], notification_id: str) -> None:
        """Remove a notification ID from storage and notify listeners."""
        async with entry_data["storage_lock"]:
            ids = entry_data["notification_ids"]
            if notification_id in ids:
                ids.remove(notification_id)
                await entry_data["store"].async_save({"ids": ids})
        # Notify listeners (sensors) of the update
        for listener in entry_data["update_listeners"]:
            listener()

    async def async_notify_fixed(call: ServiceCall) -> None:
        """Send a fixed notification."""
        # Validate notification ID is provided
        notification_id = call.data.get(ATTR_ID)
        if not notification_id or not notification_id.strip():
            raise ServiceValidationError(
                "Notification ID is required. Please provide a unique ID to identify this notification.",
                translation_domain=DOMAIN,
                translation_key="id_required",
            )

        client = _get_client(call.data)
        entry_data = _get_entry_data_from_client(client)
        defaults = {
            "default_shape": entry_data.get("default_shape", "rounded") if entry_data else "rounded",
        }
        data = _build_fixed_notification_data(call.data, defaults)
        success = await client.send_fixed_notification(data)

        if not success:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="notification_failed",
            )

        # Store the notification ID if successful and ID was provided
        if data.get("id") and entry_data:
            await _add_notification_id(entry_data, data["id"])

    async def async_clear_fixed(call: ServiceCall) -> None:
        """Clear a fixed notification."""
        client = _get_client(call.data)
        notification_id = call.data[ATTR_ID]
        success = await client.clear_fixed_notification(notification_id)

        if not success:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="clear_failed",
            )

        # Remove the notification ID from storage if successful
        entry_data = _get_entry_data_from_client(client)
        if entry_data:
            await _remove_notification_id(entry_data, notification_id)

    hass.services.async_register(
        DOMAIN, SERVICE_NOTIFY, async_notify, schema=NOTIFY_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_NOTIFY_FIXED, async_notify_fixed, schema=NOTIFY_FIXED_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CLEAR_FIXED, async_clear_fixed, schema=CLEAR_FIXED_SCHEMA
    )


def _build_notification_data(
    data: dict[str, Any], defaults: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build notification payload from service call data."""
    payload: dict[str, Any] = {}
    defaults = defaults or {}

    # Simple string fields
    simple_fields = {
        ATTR_ID: "id",
        ATTR_TITLE: "title",
        ATTR_MESSAGE: "message",
        ATTR_SOURCE: "source",
        ATTR_DURATION: "duration",
    }

    for attr, api_key in simple_fields.items():
        if attr in data and data[attr] is not None:
            payload[api_key] = data[attr]

    # Corner - use hot_corner default if not specified
    if ATTR_CORNER in data and data[ATTR_CORNER] is not None:
        payload["corner"] = data[ATTR_CORNER]
    elif defaults.get("hot_corner"):
        payload["corner"] = defaults["hot_corner"]

    # Small icon (API expects camelCase)
    if ATTR_SMALL_ICON in data and data[ATTR_SMALL_ICON]:
        payload["smallIcon"] = data[ATTR_SMALL_ICON]

    # Small icon color (hex string or color name, API expects camelCase)
    small_icon_color = _normalize_hex_color(data.get(ATTR_SMALL_ICON_COLOR))
    if small_icon_color:
        payload["smallIconColor"] = small_icon_color

    # Large icon (API expects camelCase)
    if ATTR_LARGE_ICON in data and data[ATTR_LARGE_ICON]:
        payload["largeIcon"] = data[ATTR_LARGE_ICON]

    # Media (image or video based on type)
    media_type = data.get(ATTR_MEDIA_TYPE)
    media_url = data.get(ATTR_MEDIA_URL)
    if media_url and media_type and media_type != "none":
        if media_type == "image":
            payload["image"] = media_url
        elif media_type == "video":
            payload["video"] = media_url

    return payload


def _build_fixed_notification_data(
    data: dict[str, Any], defaults: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build fixed notification payload from service call data."""
    payload: dict[str, Any] = {}
    defaults = defaults or {}

    # Simple fields
    simple_fields = {
        ATTR_ID: "id",
        ATTR_VISIBLE: "visible",
        ATTR_MESSAGE: "message",
        ATTR_EXPIRATION: "expiration",
    }

    for attr, api_key in simple_fields.items():
        if attr in data and data[attr] is not None:
            payload[api_key] = data[attr]

    # Shape - use default if not specified
    if ATTR_SHAPE in data and data[ATTR_SHAPE] is not None:
        payload["shape"] = data[ATTR_SHAPE]
    elif defaults.get("default_shape"):
        payload["shape"] = defaults["default_shape"]

    # Icon
    if ATTR_ICON in data and data[ATTR_ICON]:
        payload["icon"] = data[ATTR_ICON]

    # Colors (hex strings, API expects camelCase)
    message_color = _normalize_hex_color(data.get(ATTR_MESSAGE_COLOR))
    if message_color:
        payload["messageColor"] = message_color

    icon_color = _normalize_hex_color(data.get(ATTR_ICON_COLOR))
    if icon_color:
        payload["iconColor"] = icon_color

    border_color = _normalize_hex_color(data.get(ATTR_BORDER_COLOR))
    if border_color:
        payload["borderColor"] = border_color

    # Background color with opacity (ARGB format, API expects camelCase)
    bg_color = data.get(ATTR_BACKGROUND_COLOR)
    if bg_color:
        bg_opacity = data.get(ATTR_BACKGROUND_OPACITY)
        payload["backgroundColor"] = _hex_with_alpha(bg_color, bg_opacity)

    return payload
