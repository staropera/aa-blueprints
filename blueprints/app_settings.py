from .utils import clean_setting

# put your app settings here

"""
EXAMPLE_SETTING_ONE = getattr(
    settings,
    'EXAMPLE_SETTING_ONE',
    None
)
"""


BLUEPRINTS_ESI_TIMEOUT_ENABLED = clean_setting("BLUEPRINTS_ESI_TIMEOUT_ENABLED", True)

BLUEPRINTS_ESI_ERROR_LIMIT_THRESHOLD = clean_setting(
    "BLUEPRINTS_ESI_ERROR_LIMIT_THRESHOLD", 25
)

BLUEPRINTS_ADMIN_NOTIFICATIONS_ENABLED = clean_setting(
    "BLUEPRINTS_ADMIN_NOTIFICATIONS_ENABLED", True
)

# Hard timeout for tasks in seconds to reduce task accumulation during outages
BLUEPRINTS_TASKS_TIME_LIMIT = clean_setting("BLUEPRINTS_TASKS_TIME_LIMIT", 7200)

# Default page size for BLUEPRINT list.
# Must be an integer value from the current options as seen in the app.
BLUEPRINTS_DEFAULT_PAGE_LENGTH = clean_setting("BLUEPRINTS_DEFAULT_PAGE_LENGTH", 10)

# Wether paging is enabled for the BLUEPRINT list
BLUEPRINTS_PAGING_ENABLED = clean_setting("BLUEPRINTS_PAGING_ENABLED", True)
BLUEPRINTS_LIST_ICON_OUTPUT_SIZE = clean_setting("BLUEPRINTS_LIST_ICON_OUTPUT_SIZE", 32)

# Hours after a existing location (e.g. structure) becomes stale and gets updated
# e.g. for name changes of structures
BLUEPRINTS_LOCATION_STALE_HOURS = clean_setting("BLUEPRINTS_LOCATION_STALE_HOURS", 24)
