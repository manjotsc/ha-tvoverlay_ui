"""Constants for the TvOverlay integration."""
from typing import Final

DOMAIN: Final = "tvoverlay_ui"

# Config keys
CONF_DEVICE_IDENTIFIER: Final = "device_identifier"

# Defaults
DEFAULT_PORT: Final = 5001
DEFAULT_NAME: Final = "TvOverlay"
DEFAULT_TIMEOUT: Final = 10
DEFAULT_SCAN_INTERVAL: Final = 30

# API Endpoints
ENDPOINT_NOTIFY: Final = "/notify"
ENDPOINT_NOTIFY_FIXED: Final = "/notify_fixed"
ENDPOINT_GET: Final = "/get"
ENDPOINT_SET_OVERLAY: Final = "/set/overlay"
ENDPOINT_SET_NOTIFICATIONS: Final = "/set/notifications"
ENDPOINT_SET_SETTINGS: Final = "/set/settings"

# Notification corners
CORNER_BOTTOM_START: Final = "bottom_start"
CORNER_BOTTOM_END: Final = "bottom_end"
CORNER_TOP_START: Final = "top_start"
CORNER_TOP_END: Final = "top_end"

VALID_CORNERS: Final[list[str]] = [
    CORNER_TOP_START,
    CORNER_TOP_END,
    CORNER_BOTTOM_START,
    CORNER_BOTTOM_END,
]

# Fixed notification shapes
SHAPE_CIRCLE: Final = "circle"
SHAPE_ROUNDED: Final = "rounded"
SHAPE_RECTANGULAR: Final = "rectangular"

VALID_SHAPES: Final[list[str]] = [
    SHAPE_CIRCLE,
    SHAPE_ROUNDED,
    SHAPE_RECTANGULAR,
]

# Platforms
PLATFORMS: Final[list[str]] = [
    "binary_sensor",
    "number",
    "select",
    "sensor",
    "switch",
]

# Storage
STORAGE_KEY: Final = "tvoverlay_ui_notification_ids"
STORAGE_VERSION: Final = 1

# Service names
SERVICE_NOTIFY: Final = "notify"
SERVICE_NOTIFY_FIXED: Final = "notify_fixed"
SERVICE_CLEAR_FIXED: Final = "clear_fixed"

# Attribute keys for services
ATTR_DEVICE_ID: Final = "device_id"
ATTR_TARGET: Final = "target"
ATTR_HOST: Final = "host"
ATTR_TITLE: Final = "title"
ATTR_MESSAGE: Final = "message"
ATTR_SOURCE: Final = "source"
ATTR_CORNER: Final = "corner"
ATTR_DURATION: Final = "duration"
ATTR_ID: Final = "id"
ATTR_VISIBLE: Final = "visible"
ATTR_SHAPE: Final = "shape"
ATTR_EXPIRATION: Final = "expiration"

# Icon attributes
ATTR_SMALL_ICON: Final = "smallIcon"
ATTR_SMALL_ICON_COLOR: Final = "smallIconColor"
ATTR_LARGE_ICON: Final = "largeIcon"

# Media attributes
ATTR_MEDIA_TYPE: Final = "mediaType"
ATTR_MEDIA_URL: Final = "mediaUrl"

# Fixed notification icon attributes
ATTR_ICON: Final = "icon"
ATTR_ICON_COLOR: Final = "iconColor"

# Color attributes
ATTR_MESSAGE_COLOR: Final = "messageColor"
ATTR_BORDER_COLOR: Final = "borderColor"
ATTR_BACKGROUND_COLOR: Final = "backgroundColor"
ATTR_BACKGROUND_OPACITY: Final = "backgroundOpacity"
