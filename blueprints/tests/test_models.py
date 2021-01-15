from unittest.mock import patch

from allianceauth.eveonline.models import EveCharacter
from allianceauth.tests.auth_utils import AuthUtils
from eveuniverse.models import EveType

from ..models import Blueprint, IndustryJob, Location
from . import add_character_to_user, create_owner
from .testdata.esi_client_stub import esi_client_stub
from .testdata.load_entities import load_entities
from .testdata.load_eveuniverse import load_eveuniverse
from .testdata.load_locations import load_locations
from .utils import NoSocketsTestCase

MANAGERS_PATH = "blueprints.managers"
MODELS_PATH = "blueprints.models"


@patch(MODELS_PATH + ".esi")
@patch(MANAGERS_PATH + ".esi")
@patch("eveuniverse.managers.esi")
class TestCorporateOwner(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_entities()
        load_eveuniverse()
        load_locations()

    def setUp(self) -> None:
        self.owner = create_owner(character_id=1101, corporation_id=2101)

    def test_update_locations_esi(
        self, mock_eveuniverse_managers, mock_esi_managers, mock_esi_models
    ):
        mock_eveuniverse_managers.client = esi_client_stub
        mock_esi_managers.client = esi_client_stub
        mock_esi_models.client = esi_client_stub

        self.owner.update_locations_esi()

        self.assertEquals(
            Location.objects.get(id=1100000000001).parent,
            Location.objects.get(id=60003760),
        )

    def test_update_blueprints_esi(
        self, mock_eveuniverse_managers, mock_esi_managers, mock_esi_models
    ):
        mock_eveuniverse_managers.client = esi_client_stub
        mock_esi_managers.client = esi_client_stub
        mock_esi_models.client = esi_client_stub
        self.owner.update_blueprints_esi()
        self.assertEquals(Blueprint.objects.filter(eve_type_id=33519).count(), 1)

    def test_update_industry_jobs_esi(
        self, mock_eveuniverse_managers, mock_esi_managers, mock_esi_models
    ):
        mock_eveuniverse_managers.client = esi_client_stub
        mock_esi_managers.client = esi_client_stub
        mock_esi_models.client = esi_client_stub
        self.owner.update_blueprints_esi()
        self.owner.update_industry_jobs_esi()
        self.assertEquals(IndustryJob.objects.count(), 1)


@patch(MODELS_PATH + ".esi")
@patch(MANAGERS_PATH + ".esi")
@patch("eveuniverse.managers.esi")
class TestPersonalOwner(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_entities()
        load_eveuniverse()
        load_locations()

    def setUp(self) -> None:
        self.owner = create_owner(character_id=1101, corporation_id=None)

    def test_update_locations_esi(
        self, mock_eveuniverse_managers, mock_esi_managers, mock_esi_models
    ):
        mock_eveuniverse_managers.client = esi_client_stub
        mock_esi_managers.client = esi_client_stub
        mock_esi_models.client = esi_client_stub

        self.owner.update_locations_esi()

        self.assertEquals(
            Location.objects.get(id=1100000000001).parent,
            Location.objects.get(id=60003760),
        )

    def test_update_blueprints_esi(
        self, mock_eveuniverse_managers, mock_esi_managers, mock_esi_models
    ):
        mock_eveuniverse_managers.client = esi_client_stub
        mock_esi_managers.client = esi_client_stub
        mock_esi_models.client = esi_client_stub
        self.owner.update_blueprints_esi()
        self.assertEquals(Blueprint.objects.filter(eve_type_id=33519).count(), 1)

    def test_update_industry_jobs_esi(
        self, mock_eveuniverse_managers, mock_esi_managers, mock_esi_models
    ):
        mock_eveuniverse_managers.client = esi_client_stub
        mock_esi_managers.client = esi_client_stub
        mock_esi_models.client = esi_client_stub
        self.owner.update_blueprints_esi()
        self.owner.update_industry_jobs_esi()
        self.assertEquals(IndustryJob.objects.count(), 1)


class TestBlueprintsBase(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_entities()
        load_eveuniverse()
        load_locations()


class TestBlueprintQuerySet(TestBlueprintsBase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # given
        cls.owner_1001 = create_owner(character_id=1001, corporation_id=None)
        Blueprint.objects.create(
            location=Location.objects.get(id=60003760),
            eve_type=EveType.objects.get(id=33519),
            owner=cls.owner_1001,
            runs=10,
            location_flag="AssetSafety",
            material_efficiency=10,
            time_efficiency=30,
            item_id=1,
        )
        cls.owner_1002 = create_owner(character_id=1002, corporation_id=2001)
        Blueprint.objects.create(
            location=Location.objects.get(id=1000000000001),
            eve_type=EveType.objects.get(id=33519),
            owner=cls.owner_1002,
            location_flag="AssetSafety",
            material_efficiency=20,
            time_efficiency=40,
            item_id=2,
        )

    def test_should_annotate_is_bpo(self):
        # when
        result = Blueprint.objects.all().annotate_is_bpo().values()
        # then
        obj = result[0]
        self.assertEqual(obj["item_id"], 1)
        self.assertEqual(obj["is_bpo"], "no")
        obj = result[1]
        self.assertEqual(obj["item_id"], 2)
        self.assertEqual(obj["is_bpo"], "yes")

    def test_should_annotate_owner_name(self):
        # when
        result = Blueprint.objects.all().annotate_owner_name().values()
        # then
        obj = result[0]
        self.assertEqual(obj["item_id"], 1)
        self.assertEqual(obj["owner_name"], "Bruce Wayne")
        obj = result[1]
        self.assertEqual(obj["item_id"], 2)
        self.assertEqual(obj["owner_name"], "Wayne Technologies")


class TestBlueprintManagerUserHasAccess(TestBlueprintsBase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # given
        cls.owner_1002 = create_owner(character_id=1002, corporation_id=2001)
        Blueprint.objects.create(
            location=Location.objects.get(id=60003760),
            eve_type=EveType.objects.get(id=33519),
            owner=cls.owner_1002,
            location_flag="AssetSafety",
            material_efficiency=10,
            time_efficiency=30,
            item_id=2,
        )
        cls.owner_1003 = create_owner(character_id=1003, corporation_id=2002)
        Blueprint.objects.create(
            location=Location.objects.get(id=60003760),
            eve_type=EveType.objects.get(id=33519),
            owner=cls.owner_1003,
            location_flag="AssetSafety",
            material_efficiency=10,
            time_efficiency=30,
            item_id=3,
        )
        cls.owner_1101 = create_owner(character_id=1101, corporation_id=2101)
        Blueprint.objects.create(
            location=Location.objects.get(id=60003760),
            eve_type=EveType.objects.get(id=33519),
            owner=cls.owner_1101,
            location_flag="AssetSafety",
            material_efficiency=10,
            time_efficiency=30,
            item_id=4,
        )
        cls.owner_1102 = create_owner(character_id=1102, corporation_id=2102)
        Blueprint.objects.create(
            location=Location.objects.get(id=60003760),
            eve_type=EveType.objects.get(id=33519),
            owner=cls.owner_1102,
            location_flag="AssetSafety",
            material_efficiency=10,
            time_efficiency=30,
            item_id=5,
        )
        cls.owner_1004 = create_owner(character_id=1004, corporation_id=None)
        Blueprint.objects.create(
            location=Location.objects.get(id=60003760),
            eve_type=EveType.objects.get(id=33519),
            owner=cls.owner_1004,
            location_flag="AssetSafety",
            material_efficiency=10,
            time_efficiency=30,
            item_id=6,
        )

    def setUp(self) -> None:
        # given
        self.owner_1001 = create_owner(character_id=1001, corporation_id=None)
        self.user = self.owner_1001.character.user
        add_character_to_user(self.user, EveCharacter.objects.get(character_id=1103))
        Blueprint.objects.create(
            location=Location.objects.get(id=60003760),
            eve_type=EveType.objects.get(id=33519),
            owner=self.owner_1001,
            location_flag="AssetSafety",
            material_efficiency=10,
            time_efficiency=30,
            item_id=1,
        )

    def test_should_return_personal_and_corporation_and_alt_corporation(self):
        # when
        qs = Blueprint.objects.user_has_access(self.user)
        # then
        self.assertSetEqual(set(qs.values_list("item_id", flat=True)), {1, 2, 5})

    def test_should_return_personal_and_corporation_and_alt_corporation_and_alliance(
        self,
    ):
        # given
        self.user = AuthUtils.add_permission_to_user_by_name(
            "blueprints.view_alliance_blueprints", self.user
        )
        # when
        qs = Blueprint.objects.user_has_access(self.user)
        # then
        self.assertSetEqual(set(qs.values_list("item_id", flat=True)), {1, 2, 3, 5, 6})
