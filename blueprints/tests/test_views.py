import json

from django.http import JsonResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from eveuniverse.models import EveEntity, EveType

from ..models import Blueprint, Location, Request
from ..views import list_blueprints
from . import create_owner
from .testdata.load_entities import load_entities
from .testdata.load_eveuniverse import load_eveuniverse
from .testdata.load_locations import load_locations


def response_content_to_str(content) -> str:
    return content.decode("utf-8")


def json_response_to_python(response: JsonResponse) -> object:
    return json.loads(response_content_to_str(response.content))


class TestViewsBase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.factory = RequestFactory()
        load_eveuniverse()
        load_entities()
        load_locations()


class TestBlueprintsData(TestViewsBase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.owner = create_owner(character_id=1101, corporation_id=2101)
        cls.user = cls.owner.character.user
        cls.corporation_2001 = EveEntity.objects.get(id=2101)
        cls.jita_44 = Location.objects.get(id=60003760)

    def test_blueprints_data(self):
        Blueprint.objects.create(
            location=self.jita_44,
            eve_type=EveType.objects.get(id=33519),
            owner=self.owner,
            runs=None,
            quantity=1,
            location_flag="AssetSafety",
            material_efficiency=0,
            time_efficiency=0,
            item_id=1,
        )
        request = self.factory.get(reverse("blueprints:list_blueprints"))
        request.user = self.user
        response = list_blueprints(request)
        self.assertEqual(response.status_code, 200)
        data = json_response_to_python(response)
        self.assertEqual(len(data), 1)
        row = data[0]
        self.assertEqual(row["nme"], "Mobile Tractor Unit Blueprint")
        self.assertEqual(row["loc"], "Jita IV - Moon 4 - Caldari Navy Assembly Plant")

    def test_my_requests_data(self):
        blueprint = Blueprint.objects.create(
            location=self.jita_44,
            eve_type=EveType.objects.get(id=33519),
            owner=self.owner,
            runs=None,
            quantity=1,
            location_flag="AssetSafety",
            material_efficiency=0,
            time_efficiency=0,
            item_id=1,
        )
        Request.objects.create(
            blueprint=blueprint,
            runs=None,
            requesting_user=self.user,
            fulfulling_user=None,
            status="OP",
        )

        request = self.factory.get(reverse("blueprints:list_user_requests"))
        request.user = self.user
        response = list_blueprints(request)
        self.assertEqual(response.status_code, 200)
        data = json_response_to_python(response)
        self.assertEqual(len(data), 1)
        row = data[0]
        self.assertEqual(row["nme"], "Mobile Tractor Unit Blueprint")
        self.assertEqual(row["loc"], "Jita IV - Moon 4 - Caldari Navy Assembly Plant")
