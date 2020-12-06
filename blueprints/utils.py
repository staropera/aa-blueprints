import logging
import os
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Permission, User
from django.contrib.messages.constants import DEBUG, ERROR, INFO, SUCCESS, WARNING
from django.db.models import Q
from django.utils.html import format_html

from allianceauth.notifications import notify
from allianceauth.services.hooks import get_extension_logger

from . import __title__


class LoggerAddTag(logging.LoggerAdapter):
    """add custom tag to a logger"""

    def __init__(self, my_logger, prefix):
        super(LoggerAddTag, self).__init__(my_logger, {})
        self.prefix = prefix

    def process(self, msg, kwargs):
        return "[%s] %s" % (self.prefix, msg), kwargs


def make_logger_prefix(tag: str):
    """creates a function to add logger prefix, which returns tag when used empty"""
    return lambda text="": "{}{}".format(tag, (": " + text) if text else "")


logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class messages_plus:
    """Pendant to Django messages adding level icons and HTML support

    Careful: Use with safe strings only
    """

    _glyph_map = {
        DEBUG: "eye-open",
        INFO: "info-sign",
        SUCCESS: "ok-sign",
        WARNING: "exclamation-sign",
        ERROR: "alert",
    }

    @classmethod
    def _add_messages_icon(cls, level: int, message: str) -> str:
        """Adds an level based icon to standard Django messages"""
        if level not in cls._glyph_map:
            raise ValueError("glyph for level not defined")
        else:
            glyph = cls._glyph_map[level]

        return format_html(
            '<span class="glyphicon glyphicon-{}" '
            'aria-hidden="true"></span>&nbsp;&nbsp;{}',
            glyph,
            message,
        )

    @classmethod
    def debug(
        cls,
        request: object,
        message: str,
        extra_tags: str = "",
        fail_silently: bool = False,
    ):
        messages.debug(
            request, cls._add_messages_icon(DEBUG, message), extra_tags, fail_silently
        )

    @classmethod
    def info(
        cls,
        request: object,
        message: str,
        extra_tags: str = "",
        fail_silently: bool = False,
    ):
        messages.info(
            request, cls._add_messages_icon(INFO, message), extra_tags, fail_silently
        )

    @classmethod
    def success(
        cls,
        request: object,
        message: str,
        extra_tags: str = "",
        fail_silently: bool = False,
    ):
        messages.success(
            request, cls._add_messages_icon(SUCCESS, message), extra_tags, fail_silently
        )

    @classmethod
    def warning(
        cls,
        request: object,
        message: str,
        extra_tags: str = "",
        fail_silently: bool = False,
    ):
        messages.warning(
            request, cls._add_messages_icon(WARNING, message), extra_tags, fail_silently
        )

    @classmethod
    def error(
        cls,
        request: object,
        message: str,
        extra_tags: str = "",
        fail_silently: bool = False,
    ):
        messages.error(
            request, cls._add_messages_icon(ERROR, message), extra_tags, fail_silently
        )


def notify_admins(message: str, title: str, level="info") -> None:
    """send notification to all admins"""
    try:
        perm = Permission.objects.get(codename="logging_notifications")
        users = User.objects.filter(
            Q(groups__permissions=perm)
            | Q(user_permissions=perm)
            | Q(is_superuser=True)
        ).distinct()

        for user in users:
            notify(user, title=title, message=message, level=level)
    except Permission.DoesNotExist:
        pass


def clean_setting(
    name: str,
    default_value: object,
    min_value: int = None,
    max_value: int = None,
    required_type: type = None,
    choices: list = None,
) -> Any:
    """cleans the input for a custom setting

    Will use `default_value` if settings does not exit or has the wrong type
    or is outside define boundaries (for int only)

    Need to define `required_type` if `default_value` is `None`

    Will assume `min_value` of 0 for int (can be overriden)

    `None` allowed as value

    Returns cleaned value for setting
    """
    if default_value is None and not required_type:
        raise ValueError("You must specify a required_type for None defaults")

    if not required_type:
        required_type = type(default_value)

    if min_value is None and required_type == int:
        min_value = 0

    if not hasattr(settings, name):
        cleaned_value = default_value
    else:
        dirty_value = getattr(settings, name)
        if dirty_value is None or (
            isinstance(dirty_value, required_type)
            and (min_value is None or dirty_value >= min_value)
            and (max_value is None or dirty_value <= max_value)
            and (choices is None or dirty_value in choices)
        ):
            cleaned_value = dirty_value
        else:
            logger.warn(
                "You setting for {} it not valid. Please correct it. "
                "Using default for now: {}".format(name, default_value)
            )
            cleaned_value = default_value
    return cleaned_value


def get_swagger_spec_path() -> str:
    """returns the path to the current swagger spec file"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "swagger.json")
