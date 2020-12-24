from functools import wraps

from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError

from . import __title__
from .utils import LoggerAddTag

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def fetch_token_for_owner(scopes):
    """returns valid token for owner.
    Needs to be attached on an Owner method !!

    Args:
    -scopes: Provide the required scopes.
    """

    def decorator(func):
        @wraps(func)
        def _wrapped_view(owner, *args, **kwargs):
            token, error = owner.token(scopes)
            if error:
                raise TokenError
            logger.debug(
                "%s: Using token %s for `%s`",
                token.character_name,
                token.pk,
                func.__name__,
            )
            return func(owner, token, *args, **kwargs)

        return _wrapped_view

    return decorator
