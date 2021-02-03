import datetime as dt
from typing import Tuple

from bravado.exception import HTTPForbidden, HTTPUnauthorized
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Case, F, Q, Value, When
from django.utils.timezone import now

from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger
from esi.models import Token
from eveuniverse.models import EveEntity, EveSolarSystem, EveType

from . import __title__
from .app_settings import BLUEPRINTS_LOCATION_STALE_HOURS
from .constants import EVE_TYPE_ID_SOLAR_SYSTEM
from .helpers import fetch_esi_status
from .providers import esi
from .utils import LoggerAddTag

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class BlueprintQuerySet(models.QuerySet):
    def annotate_is_bpo(self) -> models.QuerySet:
        return self.annotate(
            is_bpo=Case(
                When(runs=None, then=Value("yes")),
                default=Value("no"),
                output_field=models.CharField(),
            )
        )

    def annotate_owner_name(self) -> models.QuerySet:
        return self.select_related(
            "owner__character__character", "owner__corporation"
        ).annotate(
            owner_name=Case(
                When(
                    owner__corporation=None,
                    then=F("owner__character__character__character_name"),
                ),
                default=F("owner__corporation__corporation_name"),
                output_field=models.CharField(),
            )
        )


class BlueprintManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return BlueprintQuerySet(self.model, using=self._db)

    def user_has_access(self, user) -> models.QuerySet:
        from .models import Owner

        corporation_ids = set(
            user.character_ownerships.select_related("character").values_list(
                "character__corporation_id", flat=True
            )
        )
        if user.has_perm("blueprints.view_alliance_blueprints"):
            alliance_ids = list(
                EveAllianceInfo.objects.filter(
                    evecorporationinfo__corporation_id__in=corporation_ids
                ).values_list("id", flat=True)
            )  # we use the django ID here to avoid a join later
            corporation_ids = corporation_ids | set(
                EveCorporationInfo.objects.filter(
                    alliance_id__in=alliance_ids
                ).values_list("corporation_id", flat=True)
            )

        personal_owner_ids = [
            owner.pk
            for owner in Owner.objects.filter(corporation__isnull=True)
            if owner.character.character.corporation_id in corporation_ids
        ]
        blueprints_query = (
            self.filter(
                Q(owner__corporation__corporation_id__in=corporation_ids)
                | Q(owner__pk__in=personal_owner_ids)
            )
            .select_related(
                "eve_type",
                "location",
                "industryjob",
                "owner",
                "owner__corporation",
                "owner__character",
                "location",
                "location__eve_solar_system",
                "location__eve_type",
            )
            .annotate(
                location__name_plus=Case(
                    When(
                        Q(location__name="") & ~Q(location__parent=None),
                        then=F("location__parent__name"),
                    ),
                    default=F("location__name"),
                    output_field=models.CharField(),
                )
            )
        )
        return blueprints_query


class LocationQuerySet(models.QuerySet):
    def annotate_name_plus(self) -> models.QuerySet:
        return self.annotate(
            name_plus=Case(
                When(Q(name="") & ~Q(parent=None), then=F("parent__name")),
                default=F("name"),
                output_field=models.CharField(),
            )
        )


class LocationManager(models.Manager):
    """Manager for Location model

    We recommend preferring the "async" variants, because it includes protection
    against exceeding the ESI error limit due to characters no longer having access
    to structures within their assets, contracts, etc.

    The async methods will first create an empty location and then try to
    update that empty location asynchronously from ESI.
    Updates might be delayed if the error limit is reached.

    The async method can also be used safely in mass updates, where the same
    unauthorized update might be requested multiple times.
    Additional requests for the same location will be ignored within a grace period.
    """

    _UPDATE_EMPTY_GRACE_MINUTES = 5

    def get_queryset(self) -> models.QuerySet:
        return LocationQuerySet(self.model, using=self._db)

    def get_or_create_esi(self, id: int, token: Token) -> Tuple[models.Model, bool]:
        """gets or creates location object with data fetched from ESI

        Stale locations will always be updated.
        Empty locations will always be updated after grace period as passed
        """
        return self._get_or_create_esi(id=id, token=token, update_async=False)

    def get_or_create_esi_async(
        self, id: int, token: Token
    ) -> Tuple[models.Model, bool]:
        """gets or creates location object with data fetched from ESI asynchronous"""
        return self._get_or_create_esi(id=id, token=token, update_async=True)

    def _get_or_create_esi(
        self, id: int, token: Token, update_async: bool = True
    ) -> Tuple[models.Model, bool]:
        id = int(id)
        empty_threshold = now() - dt.timedelta(minutes=self._UPDATE_EMPTY_GRACE_MINUTES)
        stale_threshold = now() - dt.timedelta(hours=BLUEPRINTS_LOCATION_STALE_HOURS)
        try:
            location = (
                self.exclude(
                    eve_type__isnull=True,
                    eve_solar_system__isnull=True,
                    updated_at__lt=empty_threshold,
                )
                .exclude(updated_at__lt=stale_threshold)
                .get(id=id)
            )
            created = False
        except self.model.DoesNotExist:
            if update_async:
                location, created = self.update_or_create_esi_async(id=id, token=token)
            else:
                location, created = self.update_or_create_esi(id=id, token=token)

        return location, created

    def update_or_create_esi_async(
        self, id: int, token: Token
    ) -> Tuple[models.Model, bool]:
        """updates or creates location object with data fetched from ESI asynchronous"""
        return self._update_or_create_esi(id=id, token=token, update_async=True)

    def update_or_create_esi(self, id: int, token: Token) -> Tuple[models.Model, bool]:
        """updates or creates location object with data fetched from ESI synchronous

        The preferred method to use is: `update_or_create_esi_async()`,
        since it protects against exceeding the ESI error limit and which can happen
        a lot due to users not having authorization to access a structure.
        """
        return self._update_or_create_esi(id=id, token=token, update_async=False)

    def _update_or_create_esi(
        self, id: int, token: Token, update_async: bool = True
    ) -> Tuple[models.Model, bool]:
        id = int(id)
        if self.model.is_solar_system_id(id):
            eve_solar_system, _ = EveSolarSystem.objects.get_or_create_esi(id=id)
            eve_type, _ = EveType.objects.get_or_create_esi(id=EVE_TYPE_ID_SOLAR_SYSTEM)
            location, created = self.update_or_create(
                id=id,
                defaults={
                    "name": eve_solar_system.name,
                    "eve_solar_system": eve_solar_system,
                    "eve_type": eve_type,
                },
            )
        elif self.model.is_station_id(id):
            logger.info("%s: Fetching station from ESI", id)
            station = esi.client.Universe.get_universe_stations_station_id(
                station_id=id
            ).results()
            location, created = self._station_update_or_create_dict(
                id=id, station=station
            )

        elif self.model.is_structure_id(id):
            if update_async:
                location, created = self._structure_update_or_create_esi_async(
                    id=id, token=token
                )
            else:
                location, created = self.structure_update_or_create_esi(
                    id=id, token=token
                )
        else:
            logger.warning(
                "%s: Creating empty location for ID not matching any known pattern:", id
            )
            location, created = self.get_or_create(id=id)

        return location, created

    def _station_update_or_create_dict(
        self, id: int, station: dict
    ) -> Tuple[models.Model, bool]:
        if station.get("system_id"):
            eve_solar_system, _ = EveSolarSystem.objects.get_or_create_esi(
                id=station.get("system_id")
            )
        else:
            eve_solar_system = None

        if station.get("type_id"):
            eve_type, _ = EveType.objects.get_or_create_esi(id=station.get("type_id"))
        else:
            eve_type = None

        if station.get("owner"):
            owner, _ = EveEntity.objects.get_or_create_esi(id=station.get("owner"))
        else:
            owner = None

        return self.update_or_create(
            id=id,
            defaults={
                "name": station.get("name", ""),
                "eve_solar_system": eve_solar_system,
                "eve_type": eve_type,
                "owner": owner,
            },
        )

    def _structure_update_or_create_esi_async(self, id: int, token: Token):
        from .tasks import DEFAULT_TASK_PRIORITY
        from .tasks import update_structure_esi as task_update_structure_esi

        id = int(id)
        location, created = self.get_or_create(id=id)
        task_update_structure_esi.apply_async(
            kwargs={"id": id, "token_pk": token.pk},
            priority=DEFAULT_TASK_PRIORITY,
        )
        return location, created

    def structure_update_or_create_esi(self, id: int, token: Token):
        """Update or creates structure from ESI"""
        fetch_esi_status().raise_for_status()
        try:
            structure = esi.client.Universe.get_universe_structures_structure_id(
                structure_id=id, token=token.valid_access_token()
            ).results()
        except (HTTPUnauthorized, HTTPForbidden) as http_error:
            logger.warn(
                "%s: No access to structure #%s: %s",
                token.character_name,
                id,
                http_error,
            )
            location, created = self.get_or_create(id=id)
        else:
            location, created = self._structure_update_or_create_dict(
                id=id, structure=structure
            )
        return location, created

    def _structure_update_or_create_dict(
        self, id: int, structure: dict
    ) -> Tuple[models.Model, bool]:
        """creates a new Location object from a structure dict"""
        if structure.get("solar_system_id"):
            eve_solar_system, _ = EveSolarSystem.objects.get_or_create_esi(
                id=structure.get("solar_system_id")
            )
        else:
            eve_solar_system = None

        if structure.get("type_id"):
            eve_type, _ = EveType.objects.get_or_create_esi(id=structure.get("type_id"))
        else:
            eve_type = None

        if structure.get("owner_id"):
            owner, _ = EveEntity.objects.get_or_create_esi(id=structure.get("owner_id"))
        else:
            owner = None

        return self.update_or_create(
            id=id,
            defaults={
                "name": structure.get("name", ""),
                "eve_solar_system": eve_solar_system,
                "eve_type": eve_type,
                "owner": owner,
            },
        )


class RequestQuerySet(models.QuerySet):
    def requests_fulfillable_by_user(self, user: User) -> models.QuerySet:
        ownerships = user.character_ownerships.all()
        corporation_ids = {
            character.character.corporation_id for character in ownerships
        }
        character_ownership_ids = {character.pk for character in ownerships}
        request_query = self.select_related(
            "blueprint__owner", "blueprint__owner__corporation"
        ).filter(
            (
                Q(blueprint__owner__corporation__corporation_id__in=corporation_ids)
                | Q(blueprint__owner__character__pk__in=character_ownership_ids)
            )
            & Q(closed_at=None)
            & Q(status="OP")
        )
        return request_query

    def requests_being_fulfilled_by_user(self, user: User) -> models.QuerySet:
        ownerships = user.character_ownerships.all()
        corporation_ids = {
            character.character.corporation_id for character in ownerships
        }
        character_ownership_ids = {character.pk for character in ownerships}
        request_query = self.select_related(
            "blueprint__owner", "blueprint__owner__corporation"
        ).filter(
            (
                Q(blueprint__owner__corporation__corporation_id__in=corporation_ids)
                | Q(blueprint__owner__character__pk__in=character_ownership_ids)
            )
            & Q(closed_at=None)
            & Q(status="IP")
            & Q(fulfulling_user=user)
        )
        return request_query


class RequestManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return RequestQuerySet(self.model, using=self._db)

    def select_related_default(self) -> models.QuerySet:
        return self.select_related(
            "blueprint",
            "blueprint__owner",
            "blueprint__eve_type",
            "requesting_user__profile__main_character",
        )
