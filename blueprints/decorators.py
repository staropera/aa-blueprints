from functools import wraps

from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError

from . import __title__
from .utils import LoggerAddTag

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def fetch_token_for_owner(
    scopes=[
        "esi-universe.read_structures.v1",
        "esi-corporations.read_blueprints.v1",
        "esi-assets.read_corporation_assets.v1",
    ]
):
    """returns valid token for owner.
    Needs to be attached on an Owner method !!

    Args:
    -scopes: Optionally provide the required scopes.
    Otherwise will use all scopes defined for this character.
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
