from typing import Tuple

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.evelinks import dotlan
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenExpiredError, TokenInvalidError
from esi.models import Token
from eveuniverse.models import EveEntity, EveSolarSystem, EveType

from . import __title__
from .constants import EVE_LOCATION_FLAGS
from .decorators import fetch_token_for_owner
from .managers import BlueprintManager, LocationManager, RequestManager
from .providers import esi
from .utils import LoggerAddTag, make_logger_prefix
from .validators import validate_material_efficiency, validate_time_efficiency

NAMES_MAX_LENGTH = 100

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class General(models.Model):
    """Meta model for app permissions"""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can access this app"),
            ("request_blueprints", "Can request blueprints"),
            ("manage_requests", "Can review and accept blueprint requests"),
            ("add_personal_blueprint_owner", "Can add personal blueprint owners"),
            ("add_corporate_blueprint_owner", "Can add corporate blueprint owners"),
            ("view_alliance_blueprints", "Can view alliance's blueprints"),
            ("view_blueprint_locations", "Can view the location of all blueprints"),
            ("view_industry_jobs", "Can view details about running industry jobs"),
        )


class Owner(models.Model):
    """A corporation that owns blueprints"""

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
        default=None,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text="Corporation owning blueprints, if this is a 'corporate' owner",
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
    is_active = models.BooleanField(
        default=True,
        help_text=("whether this owner is currently included in the sync process"),
    )

    class Meta:
        default_permissions = ()

    @property
    def name(self) -> str:
        if self.corporation:
            return self.corporation.corporation_name
        else:
            return self.character.character.character_name

    def update_locations_esi(self):
        if self.corporation:
            assets = self._fetch_corporate_assets()
            token = self.token(
                [
                    "esi-universe.read_structures.v1",
                    "esi-assets.read_corporation_assets.v1",
                ]
            )[0]
        else:
            assets = self._fetch_personal_assets()
            token = self.token(
                ["esi-universe.read_structures.v1", "esi-assets.read_assets.v1"]
            )[0]

        asset_ids = []
        asset_locations = {}
        assets_by_id = {}
        for asset in assets:
            asset_ids.append(asset["item_id"])
            assets_by_id[asset["item_id"]] = asset
        for asset in assets:
            if asset["location_id"] in asset_ids:
                location_id = asset["location_id"]
                if asset_locations.get(location_id):
                    asset_locations[location_id].append(asset["item_id"])
                else:
                    asset_locations[location_id] = [asset["item_id"]]
        for location in list(asset_locations.keys()):
            if not Location.objects.filter(id=location).count() > 0:
                parent_location = assets_by_id[location]["location_id"]
                Location.objects.create(
                    id=location,
                    parent=self._fetch_location(parent_location, token=token),
                    eve_type=EveType.objects.filter(
                        id=assets_by_id[location]["type_id"]
                    ).first(),
                )
            else:
                parent_location = assets_by_id[location]["location_id"]
                location_obj = Location.objects.filter(id=location).first()
                location_obj.parent = self._fetch_location(parent_location, token=token)
                location_obj.save()

    def update_blueprints_esi(self):
        """updates all blueprints from ESI"""

        if self.is_active:
            blueprint_ids_to_remove = list(
                Blueprint.objects.filter(owner=self).values_list("item_id", flat=True)
            )
            if self.corporation:
                blueprints = self._fetch_corporate_blueprints()
                token = self.token(
                    [
                        "esi-universe.read_structures.v1",
                        "esi-corporations.read_blueprints.v1",
                    ]
                )[0]
            else:
                blueprints = self._fetch_personal_blueprints()
                token = self.token(
                    [
                        "esi-universe.read_structures.v1",
                        "esi-characters.read_blueprints.v1",
                    ]
                )[0]

            for blueprint in blueprints:
                runs = blueprint["runs"]
                if runs < 1:
                    runs = None
                quantity = blueprint["quantity"]
                if quantity < 0:
                    quantity = 1
                original = Blueprint.objects.filter(
                    owner=self, item_id=blueprint["item_id"]
                ).first()
                if original is not None:
                    # We've seen this blueprint coming from ESI, so we know it shouldn't be deleted
                    blueprint_ids_to_remove.remove(original.item_id)
                    original.location = self._fetch_location(
                        blueprint["location_id"],
                        token=token,
                    )
                    original.location_flag = blueprint["location_flag"]
                    original.eve_type = EveType.objects.get_or_create_esi(
                        id=blueprint["type_id"]
                    )[0]
                    original.runs = runs
                    original.material_efficiency = blueprint["material_efficiency"]
                    original.time_efficiency = blueprint["time_efficiency"]
                    original.quantity = quantity
                    original.save()
                else:
                    Blueprint.objects.create(
                        owner=self,
                        location=self._fetch_location(
                            blueprint["location_id"],
                            token=token,
                        ),
                        location_flag=blueprint["location_flag"],
                        eve_type=EveType.objects.get_or_create_esi(
                            id=blueprint["type_id"]
                        )[0],
                        item_id=blueprint["item_id"],
                        runs=runs,
                        material_efficiency=blueprint["material_efficiency"],
                        time_efficiency=blueprint["time_efficiency"],
                        quantity=quantity,
                    )
            Blueprint.objects.filter(pk__in=blueprint_ids_to_remove).delete()

    def update_industry_jobs_esi(self):
        """updates all blueprints from ESI"""

        if self.is_active:
            job_ids_to_remove = list(
                IndustryJob.objects.filter(owner=self).values_list("id", flat=True)
            )
            if self.corporation:
                jobs = self._fetch_corporate_industry_jobs()
                token = self.token(
                    [
                        "esi-universe.read_structures.v1",
                        "esi-industry.read_corporation_jobs.v1",
                    ]
                )[0]
            else:
                jobs = self._fetch_personal_industry_jobs()
                token = self.token(
                    [
                        "esi-universe.read_structures.v1",
                        "esi-industry.read_character_jobs.v1",
                    ]
                )[0]

            for job in jobs:

                original = IndustryJob.objects.filter(
                    owner=self, id=job["job_id"]
                ).first()
                blueprint = Blueprint.objects.filter(pk=job["blueprint_id"]).first()
                if blueprint is not None:
                    if original is not None:
                        # We've seen this job coming from ESI, so we know it shouldn't be deleted
                        job_ids_to_remove.remove(original.id)
                        original.status = job["status"]
                        original.save()
                    else:
                        # Reject personal listings of corporate jobs and visa-versa
                        if blueprint.owner == self:
                            installer = EveCharacter.objects.get_character_by_id(
                                job["installer_id"]
                            )
                            if not installer:
                                installer = EveCharacter.objects.create_character(
                                    job["installer_id"]
                                )
                            IndustryJob.objects.create(
                                id=job["job_id"],
                                activity=job["activity_id"],
                                owner=self,
                                location=self._fetch_location(
                                    job["location_id"],
                                    token=token,
                                ),
                                blueprint=Blueprint.objects.get(pk=job["blueprint_id"]),
                                installer=installer,
                                runs=job["runs"],
                                start_date=job["start_date"],
                                end_date=job["end_date"],
                                status=job["status"],
                            )
                else:
                    blueprint_id = job["blueprint_id"]
                    logger.warn(f"Unmatchable blueprint ID: {blueprint_id}")
            IndustryJob.objects.filter(pk__in=job_ids_to_remove).delete()

    @fetch_token_for_owner(["esi-assets.read_corporation_assets.v1"])
    def _fetch_corporate_assets(self, token) -> list:
        return esi.client.Assets.get_corporations_corporation_id_assets(
            corporation_id=self.corporation.corporation_id,
            token=token.valid_access_token(),
        ).results()

    @fetch_token_for_owner(["esi-assets.read_assets.v1"])
    def _fetch_personal_assets(self, token) -> list:
        return esi.client.Assets.get_characters_character_id_assets(
            character_id=self.character.character.character_id,
            token=token.valid_access_token(),
        ).results()

    @fetch_token_for_owner(["esi-corporations.read_blueprints.v1"])
    def _fetch_corporate_blueprints(self, token) -> list:

        corporation_id = self.corporation.corporation_id

        blueprints = esi.client.Corporation.get_corporations_corporation_id_blueprints(
            corporation_id=corporation_id,
            token=token.valid_access_token(),
        ).results()
        return blueprints

    @fetch_token_for_owner(["esi-characters.read_blueprints.v1"])
    def _fetch_personal_blueprints(self, token) -> list:

        character_id = self.character.character.character_id

        blueprints = esi.client.Character.get_characters_character_id_blueprints(
            character_id=character_id,
            token=token.valid_access_token(),
        ).results()
        return blueprints

    @fetch_token_for_owner(["esi-industry.read_corporation_jobs.v1"])
    def _fetch_corporate_industry_jobs(self, token) -> list:

        corporation_id = self.corporation.corporation_id

        jobs = esi.client.Industry.get_corporations_corporation_id_industry_jobs(
            corporation_id=corporation_id,
            token=token.valid_access_token(),
        ).results()
        return jobs

    @fetch_token_for_owner(["esi-industry.read_character_jobs.v1"])
    def _fetch_personal_industry_jobs(self, token) -> list:

        character_id = self.character.character.character_id

        jobs = esi.client.Industry.get_characters_character_id_industry_jobs(
            character_id=character_id,
            token=token.valid_access_token(),
        ).results()
        return jobs

    def token(self, scopes=None) -> Tuple[Token, int]:
        """returns a valid Token for the owner"""
        token = None
        error = None
        add_prefix = self._logger_prefix()

        # abort if character is not configured
        if self.character is None:
            logger.error(add_prefix("No character configured to sync"))
            error = self.ERROR_NO_CHARACTER

        # abort if character does not have sufficient permissions
        elif self.corporation and not self.character.user.has_perm(
            "blueprints.add_corporate_blueprint_owner"
        ):
            logger.error(
                add_prefix(
                    "This character does not have sufficient permission to sync corporations"
                )
            )
            error = self.ERROR_INSUFFICIENT_PERMISSIONS

        # abort if character does not have sufficient permissions
        elif not self.character.user.has_perm(
            "blueprints.add_personal_blueprint_owner"
        ):
            logger.error(
                add_prefix(
                    "This character does not have sufficient permission to sync personal blueprints"
                )
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
                    .require_scopes(scopes)
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

    def _fetch_location(self, location_id, token) -> "Location":
        return Location.objects.get_or_create_esi_async(id=location_id, token=token)[0]

    def _logger_prefix(self):
        """returns standard logger prefix function"""
        if self.corporation:
            return make_logger_prefix(self.corporation.corporation_ticker)
        else:
            return make_logger_prefix(self.character.character.character_name)

    def __str__(self):
        if self.corporation:
            return self.corporation.corporation_name
        else:
            return self.character.character.character_name


class Blueprint(models.Model):

    item_id = models.PositiveBigIntegerField(
        primary_key=True, help_text="The EVE Item ID of the blueprint"
    )
    owner = models.ForeignKey(
        Owner,
        on_delete=models.CASCADE,
        help_text="Corporation that owns the blueprint",
    )
    eve_type = models.ForeignKey(
        EveType, on_delete=models.CASCADE, help_text="Blueprint type"
    )
    location = models.ForeignKey(
        "Location", on_delete=models.CASCADE, help_text="Blueprint location"
    )
    _location_flag_choices = []
    for choice in EVE_LOCATION_FLAGS:
        _location_flag_choices.append((choice, choice))

    location_flag = models.CharField(
        help_text="Additional location information",
        choices=_location_flag_choices,
        max_length=36,
    )
    quantity = models.PositiveIntegerField(help_text="Number of blueprints", default=1)
    runs = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Runs remaining or null if the blueprint is an original",
    )
    material_efficiency = models.PositiveIntegerField(
        help_text="Material efficiency of the blueprint",
        validators=[validate_material_efficiency],
    )
    time_efficiency = models.PositiveIntegerField(
        help_text="Time efficiency of the blueprint",
        validators=[validate_time_efficiency],
    )

    objects = BlueprintManager()

    @property
    def is_original(self):
        return not self.runs

    class Meta:
        default_permissions = ()

    def __str__(self):
        return (
            self.eve_type.name + f" ({self.material_efficiency}/{self.time_efficiency})"
        )

    def has_industryjob(self):
        return hasattr(self, "industryjob") and self.industryjob is not None


class IndustryJob(models.Model):
    id = models.PositiveBigIntegerField(
        primary_key=True,
        help_text=("Eve Online job ID"),
    )

    class Activity(models.IntegerChoices):
        MANUFACTURING = 1, _("Manufacturing")
        RESEARCHING_TECHNOLOGY = 2, _("Researching Technology")
        RESEARCHING_TIME_EFFICIENCY = 3, _("Researching Time Efficiency")
        RESEARCHING_MATERIAL_EFFICIENCY = 4, _("Researching Material Efficiency")
        COPYING = 5, _("Copying")
        DUPLICATING = 6, _("Duplicating")
        REVERSE_ENGINEERING = 7, _("Reverse Engineering")
        INVENTING = 8, _("Inventing")
        REACTING = 9, _("Reacting")

    activity = models.PositiveIntegerField(choices=Activity.choices)
    location = models.ForeignKey(
        "Location",
        on_delete=models.CASCADE,
        help_text=(
            "Eve Online location ID of the facility in which the job is running"
        ),
        related_name="+",
    )
    blueprint = models.OneToOneField(
        Blueprint,
        on_delete=models.CASCADE,
        help_text=("Blueprint the job is running"),
    )
    installer = models.ForeignKey(
        EveCharacter,
        on_delete=models.CASCADE,
        related_name="jobs",
    )
    owner = models.ForeignKey(
        Owner,
        on_delete=models.CASCADE,
        related_name="jobs",
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    runs = models.PositiveIntegerField()
    status = models.CharField(
        choices=(
            ("active", "Active"),
            ("cancelled", "Cancelled"),
            ("delivered", "Delivered"),
            ("paused", "Paused"),
            ("ready", "Ready"),
            ("reverted", "Reverted"),
        ),
        max_length=10,
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
    parent = models.ForeignKey(
        "Location",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        help_text=("Eve Online location ID of the parent object"),
        related_name="+",
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
        return self.name_plus + f" [id={self.id}]"

    def __repr__(self) -> str:
        return "{}(id={}, name='{}')".format(
            self.__class__.__name__, self.id, self.name
        )

    @property
    def name_plus(self) -> str:
        """return the actual name or 'Unknown location' for empty locations"""
        if self.is_empty:
            return f"Unknown location #{self.id}"
        if not self.name and self.parent:
            return self.parent.name_plus
        return self.name

    @property
    def is_empty(self) -> bool:
        return not self.eve_solar_system and not self.eve_type and not self.parent_id

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


class Request(models.Model):

    objects = RequestManager()
    blueprint = models.ForeignKey(
        Blueprint,
        on_delete=models.CASCADE,
    )
    requesting_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="+",
        help_text="The requesting user",
    )
    fulfulling_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        help_text="The user that fulfilled the request, if it has been fulfilled",
    )
    runs = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Runs requested or blank for maximum allowed",
    )
    STATUS_OPEN = "OP"
    STATUS_IN_PROGRESS = "IP"
    STATUS_FULFILLED = "FL"
    STATUS_CANCELLED = "CL"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_FULFILLED, "Fulfilled"),
        (STATUS_CANCELLED, "Cancelled"),
    ]
    status = models.CharField(
        help_text="Status of the blueprint request",
        choices=STATUS_CHOICES,
        max_length=2,
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    closed_at = models.DateTimeField(blank=True, null=True, db_index=True)

    class Meta:
        default_permissions = ()

    def __str__(self) -> str:
        return f"{self.requesting_user.profile.main_character.character_name}'s request for {self.blueprint.eve_type.name}"

    def __repr__(self) -> str:
        return "{}(id={}, requesting_user='{}', type_name='{}')".format(
            self.__class__.__name__,
            self.pk,
            self.requesting_user.profile.main_character.character_name,
            self.eve_type.name,
        )
