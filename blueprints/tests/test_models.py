from unittest.mock import patch

from ..models import Blueprint, IndustryJob, Location
from . import create_owner
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
