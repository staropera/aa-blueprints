import random
from time import sleep
from typing import Optional

import requests

from allianceauth.services.hooks import get_extension_logger

from . import __title__, __version__
from .app_settings import BLUEPRINTS_ESI_ERROR_LIMIT_THRESHOLD
from .utils import LoggerAddTag

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class EsiStatusException(Exception):
    """EsiStatus base exception"""

    def __init__(self, message):
        super().__init__()
        self.message = message


class EsiOffline(EsiStatusException):
    """ESI is offline"""

    def __init__(self):
        super().__init__("ESI appears to be offline")


class EsiErrorLimitExceeded(EsiStatusException):
    """ESI error limit exceeded"""

    def __init__(self, retry_in: float) -> None:
        retry_in = float(retry_in)
        super().__init__("The ESI error limit has been exceeded.")
        self.retry_in = retry_in  # seconds until next error window


class EsiStatus:
    """Current status of ESI (immutable)"""

    MAX_JITTER = 20

    def __init__(
        self,
        is_online: bool,
        error_limit_remain: int = None,
        error_limit_reset: int = None,
    ) -> None:
        self._is_online = bool(is_online)
        if error_limit_remain is None or error_limit_reset is None:
            self._error_limit_remain = None
            self._error_limit_reset = None
        else:
            self._error_limit_remain = int(error_limit_remain)
            self._error_limit_reset = int(error_limit_reset)

    @property
    def is_online(self) -> bool:
        return self._is_online

    @property
    def error_limit_remain(self) -> Optional[int]:
        return self._error_limit_remain

    @property
    def error_limit_reset(self) -> Optional[int]:
        return self._error_limit_reset

    @property
    def is_error_limit_exceeded(self) -> bool:
        """return True if remain is below the threshold, else False.

        Will also return False if remain/reset are not defined
        """
        return bool(
            self.error_limit_remain
            and self.error_limit_reset
            and self.error_limit_remain <= BLUEPRINTS_ESI_ERROR_LIMIT_THRESHOLD
        )

    def error_limit_reset_w_jitter(self, max_jitter: int = None) -> int:
        """seconds to retry in order to reach next error window incl. jitter"""
        if self.error_limit_reset is None:
            return 0
        else:
            if not max_jitter or max_jitter < 1:
                max_jitter = self.MAX_JITTER

            return self.error_limit_reset + int(random.uniform(1, max_jitter))

    def raise_for_status(self):
        """will raise an exception derived from EsiStatusException
        if and only if conditions are met."""
        if not self.is_online:
            raise EsiOffline()

        if self.is_error_limit_exceeded:
            raise EsiErrorLimitExceeded(retry_in=self.error_limit_reset_w_jitter())


def fetch_esi_status() -> EsiStatus:
    """returns the current ESI online and error status"""
    max_retries = 3
    retries = 0
    while True:
        try:
            r = requests.get(
                "https://esi.evetech.net/latest/status/",
                timeout=(5, 30),
                headers={"User-Agent": f"{__title__};{__version__}"},
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            logger.warning("Network error when trying to call ESI", exc_info=True)
            return EsiStatus(
                is_online=False, error_limit_remain=None, error_limit_reset=None
            )
        if r.status_code not in {
            502,  # HTTPBadGateway
            503,  # HTTPServiceUnavailable
            504,  # HTTPGatewayTimeout
        }:
            break
        else:
            retries += 1
            if retries > max_retries:
                break
            else:
                logger.warning(
                    "HTTP status code %s - Retry %s/%s",
                    r.status_code,
                    retries,
                    max_retries,
                )
                wait_secs = 0.1 * (random.uniform(2, 4) ** (retries - 1))
                sleep(wait_secs)

    if not r.ok:
        is_online = False
    else:
        try:
            is_online = False if r.json().get("vip") else True
        except ValueError:
            is_online = False

    try:
        remain = int(r.headers.get("X-Esi-Error-Limit-Remain"))
        reset = int(r.headers.get("X-Esi-Error-Limit-Reset"))
    except TypeError:
        logger.warning("Failed to parse HTTP headers: %s", r.headers, exc_info=True)
        return EsiStatus(is_online=is_online)
    else:
        logger.debug(
            "ESI status: is_online: %s, error_limit_remain = %s, error_limit_reset = %s",
            is_online,
            remain,
            reset,
        )
        return EsiStatus(
            is_online=is_online, error_limit_remain=remain, error_limit_reset=reset
        )
