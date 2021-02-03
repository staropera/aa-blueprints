import json
from unittest.mock import patch

from django.http import JsonResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from allianceauth.tests.auth_utils import AuthUtils
from eveuniverse.models import EveEntity, EveType

from ..models import Blueprint, Location, Owner, Request
from ..views.blueprint_list import BlueprintListJson
from ..views.regular_views import (
    list_blueprints_ffd,
    list_user_owners,
    mark_request_cancelled,
    mark_request_fulfilled,
    mark_request_in_progress,
    mark_request_open,
    remove_owner,
)
from . import create_owner
from .testdata.load_entities import load_entities
from .testdata.load_eveuniverse import load_eveuniverse
from .testdata.load_locations import load_locations

MODELS_PATH = "blueprints.models"
VIEWS_PATH = "blueprints.views.regular_views"


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
        cls.owner.character.user = AuthUtils.add_permission_to_user_by_name(
            "blueprints.view_blueprint_locations", cls.owner.character.user
        )
        cls.user = cls.owner.character.user
        cls.corporation_2001 = EveEntity.objects.get(id=2101)
        cls.jita_44 = Location.objects.get(id=60003760)
        cls.blueprint = Blueprint.objects.create(
            location=cls.jita_44,
            eve_type=EveType.objects.get(id=33519),
            owner=cls.owner,
            runs=None,
            quantity=1,
            location_flag="AssetSafety",
            material_efficiency=0,
            time_efficiency=0,
            item_id=1,
        )

    def test_blueprints_data(self):
        request = self.factory.get(reverse("blueprints:list_blueprints"))
        request.user = self.user
        response = BlueprintListJson.as_view()(request)
        self.assertEqual(response.status_code, 200)
        data = json_response_to_python(response)["data"]
        self.assertEqual(len(data), 1)
        row = data[0]
        self.assertEqual(row[1], "Mobile Tractor Unit Blueprint")
        self.assertEqual(row[9], "Jita IV - Moon 4 - Caldari Navy Assembly Plant")

    def test_my_requests_data(self):

        Request.objects.create(
            blueprint=self.blueprint,
            runs=None,
            requesting_user=self.user,
            fulfulling_user=None,
            status="OP",
        )

        request = self.factory.get(reverse("blueprints:list_user_requests"))
        request.user = self.user
        response = BlueprintListJson.as_view()(request)
        self.assertEqual(response.status_code, 200)
        data = json_response_to_python(response)["data"]
        self.assertEqual(len(data), 1)
        row = data[0]
        self.assertEqual(row[1], "Mobile Tractor Unit Blueprint")
        self.assertEqual(row[9], "Jita IV - Moon 4 - Caldari Navy Assembly Plant")

    @patch(VIEWS_PATH + ".messages_plus")
    def test_mark_request_in_progress(self, mock_messages):

        user_request = Request.objects.create(
            blueprint=self.blueprint,
            runs=None,
            requesting_user=self.user,
            fulfulling_user=None,
            status="OP",
        )
        user_request.save()
        request = self.factory.post(
            reverse("blueprints:request_in_progress", args=[user_request.pk])
        )
        request.user = self.user
        response = mark_request_in_progress(request, user_request.pk)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(mock_messages.info.called)
        user_request.refresh_from_db()
        self.assertEquals(user_request.status, "IP")

    @patch(VIEWS_PATH + ".messages_plus")
    def test_mark_request_fulfilled(self, mock_messages):

        user_request = Request.objects.create(
            blueprint=self.blueprint,
            runs=None,
            requesting_user=self.user,
            fulfulling_user=None,
            status="IP",
        )
        user_request.save()
        request = self.factory.post(
            reverse("blueprints:request_fulfilled", args=[user_request.pk])
        )
        request.user = self.user
        response = mark_request_fulfilled(request, user_request.pk)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(mock_messages.info.called)
        user_request.refresh_from_db()
        self.assertEquals(user_request.status, "FL")
        self.assertEquals(user_request.fulfulling_user, self.user)

    @patch(VIEWS_PATH + ".messages_plus")
    def test_mark_request_cancelled(self, mock_messages):

        user_request = Request.objects.create(
            blueprint=self.blueprint,
            runs=None,
            requesting_user=self.user,
            fulfulling_user=None,
            status="IP",
        )
        user_request.save()
        request = self.factory.post(
            reverse("blueprints:request_cancelled", args=[user_request.pk])
        )
        request.user = self.user
        response = mark_request_cancelled(request, user_request.pk)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(mock_messages.info.called)
        user_request.refresh_from_db()
        self.assertEquals(user_request.status, "CL")
        self.assertEquals(user_request.fulfulling_user, None)

    @patch(VIEWS_PATH + ".messages_plus")
    def test_mark_request_open(self, mock_messages):

        user_request = Request.objects.create(
            blueprint=self.blueprint,
            runs=None,
            requesting_user=self.user,
            fulfulling_user=self.user,
            status="IP",
        )
        user_request.save()
        request = self.factory.post(
            reverse("blueprints:request_open", args=[user_request.pk])
        )
        request.user = self.user
        response = mark_request_open(request, user_request.pk)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(mock_messages.info.called)
        user_request.refresh_from_db()
        self.assertEquals(user_request.status, "OP")
        self.assertEquals(user_request.fulfulling_user, None)

    def test_list_user_owners(self):
        request = self.factory.get(reverse("blueprints:list_user_owners"))
        request.user = self.user
        response = list_user_owners(request)
        self.assertEqual(response.status_code, 200)
        data = json_response_to_python(response)
        self.assertEqual(len(data), 1)
        row = data[0]
        self.assertEqual(row["name"], "Lexcorp")
        self.assertEqual(row["type"], "corporate")

    @patch(VIEWS_PATH + ".messages_plus")
    def test_remove_owner(self, mock_messages):
        request = self.factory.post(
            reverse("blueprints:remove_owner", args=[self.owner.pk])
        )
        request.user = self.user
        response = remove_owner(request, self.owner.pk)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(mock_messages.info.called)
        self.assertEqual(Owner.objects.filter(pk=self.owner.pk).first(), None)


class TestListBlueprintsFdd(TestViewsBase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.owner_1001 = create_owner(character_id=1001, corporation_id=None)
        cls.owner_1001.character.user = AuthUtils.add_permission_to_user_by_name(
            "blueprints.view_blueprint_locations", cls.owner_1001.character.user
        )
        cls.owner_1002 = create_owner(character_id=1002, corporation_id=2001)

    def test_should_return_list_of_options(self):

        # given
        Blueprint.objects.create(
            location=Location.objects.get(id=60003760),
            eve_type=EveType.objects.get(id=33519),
            owner=self.owner_1001,
            runs=10,
            location_flag="AssetSafety",
            material_efficiency=10,
            time_efficiency=30,
            item_id=1,
        )
        Blueprint.objects.create(
            location=Location.objects.get(id=1000000000001),
            eve_type=EveType.objects.get(id=33519),
            owner=self.owner_1002,
            location_flag="AssetSafety",
            material_efficiency=20,
            time_efficiency=40,
            item_id=2,
        )
        # when
        request = self.factory.get(
            reverse("blueprints:list_blueprints_ffd")
            + "?columns=location,owner,material_efficiency,time_efficiency,is_original"
        )
        request.user = self.owner_1001.character.user
        response = list_blueprints_ffd(request)
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_python(response)
        self.assertDictEqual(
            data,
            {
                "location": [
                    "Amamake - Test Structure Alpha",
                    "Jita IV - Moon 4 - Caldari Navy Assembly Plant",
                ],
                "owner": ["Bruce Wayne", "Wayne Technologies"],
                "material_efficiency": [10, 20],
                "time_efficiency": [30, 40],
                "is_original": ["no", "yes"],
            },
        )
