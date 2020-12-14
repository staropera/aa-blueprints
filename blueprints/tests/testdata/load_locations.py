import inspect
import json
import os

from eveuniverse.models import EveEntity

from ...constants import EVE_CATEGORY_ID_STATION
from ...models import Location

_currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


def _load_data():
    with open(_currentdir + "/esi_testdata.json", "r", encoding="utf-8") as f:
        return json.load(f)


_data = _load_data()


def load_locations():
    """Loads Location objects from stations and structure defined in ESI test data"""
    for structure_id, structure in _data["Universe"][
        "get_universe_structures_structure_id"
    ].items():
        Location.objects._structure_update_or_create_dict(
            id=structure_id, structure=structure
        )

    for station_id, station in _data["Universe"][
        "get_universe_stations_station_id"
    ].items():
        Location.objects._station_update_or_create_dict(id=station_id, station=station)

    for obj in Location.objects.filter(
        eve_type__eve_group__eve_category_id=EVE_CATEGORY_ID_STATION
    ):
        EveEntity.objects.create(
            id=obj.id,
            name=obj.name,
            category=EveEntity.CATEGORY_STATION,
        )
