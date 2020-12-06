from django.db import models
from django.utils.timezone import now

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.evelinks import dotlan
from allianceauth.eveonline.models import EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError, TokenExpiredError, TokenInvalidError
from esi.models import Token
from eveuniverse.models import EveEntity, EveSolarSystem, EveType

from . import __title__
from .constants import EVE_LOCATION_FLAGS
from .managers import LocationManager
from .providers import esi
from .utils import LoggerAddTag, make_logger_prefix

NAMES_MAX_LENGTH = 100

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class Blueprints(models.Model):
    """Meta model for app permissions"""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can access this app"),
            ("add_blueprint_owner", "Can add blueprint owners"),
            ("view_alliance_blueprints", "Can view alliance's blueprints"),
        )


class Owner(models.Model):
    """A corporation that owns blueprints"""

    # errors
    ERROR_NONE = 0
    ERROR_TOKEN_INVALID = 1
    ERROR_TOKEN_EXPIRED = 2
    ERROR_INSUFFICIENT_PERMISSIONS = 3
    ERROR_NO_CHARACTER = 4
    ERROR_ESI_UNAVAILABLE = 5
    ERROR_OPERATION_MODE_MISMATCH = 6
    ERROR_UNKNOWN = 99

    ERRORS_LIST = [
        (ERROR_NONE, "No error"),
        (ERROR_TOKEN_INVALID, "Invalid token"),
        (ERROR_TOKEN_EXPIRED, "Expired token"),
        (ERROR_INSUFFICIENT_PERMISSIONS, "Insufficient permissions"),
        (ERROR_NO_CHARACTER, "No character set for fetching data from ESI"),
        (ERROR_ESI_UNAVAILABLE, "ESI API is currently unavailable"),
        (
            ERROR_OPERATION_MODE_MISMATCH,
            "Operaton mode does not match with current setting",
        ),
        (ERROR_UNKNOWN, "Unknown error"),
    ]

    corporation = models.OneToOneField(
        EveCorporationInfo,
        primary_key=True,
        on_delete=models.CASCADE,
        help_text="Corporation owning blueprints",
        related_name="+",
    )
    character = models.ForeignKey(
        CharacterOwnership,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        help_text="character used for syncing blueprints",
        related_name="+",
    )
    blueprints_last_sync = models.DateTimeField(
        null=True, default=None, blank=True, help_text="when the last sync happened"
    )
    blueprints_last_error = models.IntegerField(
        choices=ERRORS_LIST,
        default=ERROR_NONE,
        help_text="error that occurred at the last sync atttempt (if any)",
    )
    is_active = models.BooleanField(
        default=True,
        help_text=("whether this owner is currently included in the sync process"),
    )

    def update_blueprints_esi(self):
        """updates all blueprints from ESI"""

        if self.is_active:
            try:
                token, error = self.token()
                if error:
                    self.blueprints_last_error = error
                    self.blueprints_last_sync = now()
                    self.save()
                    raise TokenError(self.to_friendly_error_message(error))

                blueprints = self._fetch_blueprints(token)
            except TokenError:
                blueprints = []
            stored_blueprints = []
            Blueprint.objects.filter(owner=self).delete()
            for blueprint in blueprints:
                runs = blueprint["runs"]
                if runs < 1:
                    runs = None
                quantity = blueprint["quantity"]
                if quantity < 0:
                    quantity = 1
                duplicate = False
                for stored in stored_blueprints:
                    if (
                        stored["type_id"] == blueprint["type_id"]
                        and stored["runs"] == blueprint["runs"]
                        and stored["material_efficiency"]
                        == blueprint["material_efficiency"]
                        and stored["time_efficiency"] == blueprint["time_efficiency"]
                        and stored["location_id"] == blueprint["location_id"]
                        and stored["location_flag"] == blueprint["location_flag"]
                    ):
                        duplicate = True
                        break
                if duplicate:
                    duplicated = Blueprint.objects.filter(
                        owner=self,
                        location=Location.objects.get_or_create_esi_async(
                            blueprint["location_id"],
                            token=token,
                        )[0],
                        location_flag=blueprint["location_flag"],
                        runs=runs,
                        eve_type=blueprint["type_id"],
                        material_efficiency=blueprint["material_efficiency"],
                        time_efficiency=blueprint["time_efficiency"],
                    ).first()
                    duplicated.quantity += quantity
                    duplicated.save()
                else:
                    Blueprint.objects.create(
                        owner=self,
                        location=Location.objects.get_or_create_esi_async(
                            blueprint["location_id"],
                            token=token,
                        )[0],
                        location_flag=blueprint["location_flag"],
                        eve_type=EveType.objects.get_or_create_esi(
                            id=blueprint["type_id"]
                        )[0],
                        runs=runs,
                        material_efficiency=blueprint["material_efficiency"],
                        time_efficiency=blueprint["time_efficiency"],
                        quantity=quantity,
                    )
                    stored_blueprints.append(blueprint)

    def _fetch_blueprints(self, token: Token) -> list:
        """fetch Blueprints from ESI for self"""

        corporation_id = self.corporation.corporation_id

        # fetch all blueprints incl. localizations for services
        # blueprints = esi_fetch(
        #     esi_path="Corporation.get_corporations_corporation_id_blueprints",
        #     args={"corporation_id": corporation_id},
        #     token=token,
        #     has_pages=True,
        #     logger_tag=add_prefix(),
        # )
        blueprints = esi.client.Corporation.get_corporations_corporation_id_blueprints(
            corporation_id=corporation_id,
            token=token.valid_access_token(),
        ).results()
        return blueprints

    def token(self) -> Token:
        """returns a valid Token for the owner"""
        token = None
        error = None
        add_prefix = self._logger_prefix()

        # abort if character is not configured
        if self.character is None:
            logger.error(add_prefix("No character configured to sync"))
            error = self.ERROR_NO_CHARACTER

        # abort if character does not have sufficient permissions
        elif not self.character.user.has_perm("blueprints.add_blueprint_owner"):
            logger.error(
                add_prefix("self character does not have sufficient permission to sync")
            )
            error = self.ERROR_INSUFFICIENT_PERMISSIONS

        else:
            try:
                # get token
                token = (
                    Token.objects.filter(
                        user=self.character.user,
                        character_id=self.character.character.character_id,
                    )
                    .require_scopes(["esi-corporations.read_blueprints.v1"])
                    .require_valid()
                    .first()
                )
            except TokenInvalidError:
                logger.error(add_prefix("Invalid token for fetching blueprints"))
                error = self.ERROR_TOKEN_INVALID
            except TokenExpiredError:
                logger.error(add_prefix("Token expired for fetching blueprints"))
                error = self.ERROR_TOKEN_EXPIRED
            else:
                if not token:
                    logger.error(add_prefix("No token found with sufficient scopes"))
                    error = self.ERROR_TOKEN_INVALID

        return token, error

    def _logger_prefix(self):
        """returns standard logger prefix function"""
        return make_logger_prefix(self.corporation.corporation_ticker)

    def __str__(self):
        return self.corporation.corporation_name


class Blueprint(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="unique_blueprints",
                fields=[
                    "owner",
                    "location",
                    "location_flag",
                    "eve_type",
                    "runs",
                    "material_efficiency",
                    "time_efficiency",
                ],
            ),
        ]

    owner = models.ForeignKey(
        Owner,
        on_delete=models.CASCADE,
        help_text="Corporation that owns the blueprint",
    )
    eve_type = models.ForeignKey(
        EveType, on_delete=models.CASCADE, help_text="Blueprint Type"
    )
    location = models.ForeignKey(
        "Location", on_delete=models.CASCADE, help_text="Location of the blueprints"
    )
    _location_flag_choices = []
    for choice in EVE_LOCATION_FLAGS:
        _location_flag_choices.append((choice, choice))

    location_flag = models.CharField(
        help_text="Specific location of the blueprint",
        choices=_location_flag_choices,
        max_length=36,
    )
    quantity = models.PositiveIntegerField(help_text="Number of blueprints", default=1)
    runs = models.PositiveIntegerField(
        blank=True, null=True, help_text="Runs remaining, if applicable"
    )
    material_efficiency = models.PositiveIntegerField(
        help_text="Material efficiency of the blueprint"
    )
    time_efficiency = models.PositiveIntegerField(
        help_text="Time efficiency of the blueprint"
    )

    def __str__(self):
        return (
            self.eve_type.name + f" ({self.material_efficiency}/{self.time_efficiency})"
        )


class Location(models.Model):
    """An Eve Online location: Station or Upwell Structure or Solar System"""

    _SOLAR_SYSTEM_ID_START = 30_000_000
    _SOLAR_SYSTEM_ID_END = 33_000_000
    _STATION_ID_START = 60_000_000
    _STATION_ID_END = 64_000_000
    _STRUCTURE_ID_START = 1_000_000_000_000

    id = models.PositiveBigIntegerField(
        primary_key=True,
        help_text=(
            "Eve Online location ID, "
            "either item ID for stations or structure ID for structures"
        ),
    )
    name = models.CharField(
        max_length=NAMES_MAX_LENGTH,
        help_text="In-game name of this station or structure",
    )
    eve_solar_system = models.ForeignKey(
        EveSolarSystem,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        related_name="+",
    )
    eve_type = models.ForeignKey(
        EveType,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        related_name="+",
    )
    owner = models.ForeignKey(
        EveEntity,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        help_text="corporation this station or structure belongs to",
        related_name="+",
    )
    updated_at = models.DateTimeField(auto_now=True)

    objects = LocationManager()

    class Meta:
        default_permissions = ()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return "{}(id={}, name='{}')".format(
            self.__class__.__name__, self.id, self.name
        )

    @property
    def name_plus(self) -> str:
        """return the actual name or 'Unknown location' for empty locations"""
        if self.is_empty:
            return f"Unknown location #{self.id}"

        return self.name

    @property
    def is_empty(self) -> bool:
        return not self.eve_solar_system and not self.eve_type

    @property
    def solar_system_url(self) -> str:
        """returns dotlan URL for this solar system"""
        try:
            return dotlan.solar_system_url(self.eve_solar_system.name)
        except AttributeError:
            return ""

    @property
    def is_solar_system(self) -> bool:
        return self.is_solar_system_id(self.id)

    @property
    def is_station(self) -> bool:
        return self.is_station_id(self.id)

    @property
    def is_structure(self) -> bool:
        return self.is_structure_id(self.id)

    @classmethod
    def is_solar_system_id(cls, location_id: int) -> bool:
        return cls._SOLAR_SYSTEM_ID_START <= location_id <= cls._SOLAR_SYSTEM_ID_END

    @classmethod
    def is_station_id(cls, location_id: int) -> bool:
        return cls._STATION_ID_START <= location_id <= cls._STATION_ID_END

    @classmethod
    def is_structure_id(cls, location_id: int) -> bool:
        return location_id >= cls._STRUCTURE_ID_START
