import inspect
import json
import os

from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from eveuniverse.models import (
    EveConstellation,
    EveEntity,
    EveFaction,
    EveRegion,
    EveSolarSystem,
    EveType,
)

_currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


def _load_entities_data():
    with open(_currentdir + "/entities.json", "r", encoding="utf-8") as f:
        return json.load(f)


_entities_data = _load_entities_data()


def load_entities():
    EveAllianceInfo.objects.all().delete()
    EveCorporationInfo.objects.all().delete()
    EveCharacter.objects.all().delete()
    EveEntity.objects.all().delete()
    for character_info in _entities_data.get("EveCharacter"):
        if character_info.get("alliance_id"):
            try:
                alliance = EveAllianceInfo.objects.get(
                    alliance_id=character_info.get("alliance_id")
                )
            except EveAllianceInfo.DoesNotExist:
                alliance = EveAllianceInfo.objects.create(
                    alliance_id=character_info.get("alliance_id"),
                    alliance_name=character_info.get("alliance_name"),
                    alliance_ticker=character_info.get("alliance_ticker"),
                    executor_corp_id=character_info.get("corporation_id"),
                )
                EveEntity.objects.create(
                    id=alliance.alliance_id,
                    name=alliance.alliance_name,
                    category=EveEntity.CATEGORY_ALLIANCE,
                )
        else:
            alliance = None
        try:
            corporation = EveCorporationInfo.objects.get(
                corporation_id=character_info.get("corporation_id")
            )
        except EveCorporationInfo.DoesNotExist:
            corporation = EveCorporationInfo.objects.create(
                corporation_id=character_info.get("corporation_id"),
                corporation_name=character_info.get("corporation_name"),
                corporation_ticker=character_info.get("corporation_ticker"),
                member_count=99,
                alliance=alliance,
            )
            EveEntity.objects.create(
                id=corporation.corporation_id,
                name=corporation.corporation_name,
                category=EveEntity.CATEGORY_CORPORATION,
            )

        character = EveCharacter.objects.create(
            character_id=character_info.get("character_id"),
            character_name=character_info.get("character_name"),
            corporation_id=corporation.corporation_id,
            corporation_name=corporation.corporation_name,
            corporation_ticker=corporation.corporation_ticker,
            alliance_id=alliance.alliance_id if alliance else None,
            alliance_name=alliance.alliance_name if alliance else "",
            alliance_ticker=alliance.alliance_ticker if alliance else "",
        )
        EveEntity.objects.create(
            id=character.character_id,
            name=character.character_name,
            category=EveEntity.CATEGORY_CHARACTER,
        )

    for entity_info in _entities_data.get("EveEntity"):
        EveEntity.objects.create(
            id=entity_info.get("id"),
            name=entity_info.get("name"),
            category=entity_info.get("category"),
        )

    for EveModel in [EveConstellation, EveFaction, EveRegion, EveSolarSystem, EveType]:
        _generate_eve_entities_from_eve_universe(EveModel)


def _generate_eve_entities_from_eve_universe(EveModel):
    category = EveModel.eve_entity_category()
    for obj in EveModel.objects.all():
        EveEntity.objects.create(
            id=obj.id,
            name=obj.name,
            category=category,
        )
