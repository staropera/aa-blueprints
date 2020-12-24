from unittest.mock import patch

from django.test import TestCase, override_settings

from .. import tasks
from . import create_owner
from .testdata.load_entities import load_entities
from .testdata.load_eveuniverse import load_eveuniverse
from .testdata.load_locations import load_locations

TASKS_PATH = "blueprints.tasks"


@override_settings(CELERY_ALWAYS_EAGER=True)
class TestUpdateBlueprints(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_entities()
        load_eveuniverse()
        load_locations()
        cls.owner = create_owner(character_id=1101, corporation_id=2101)

    @patch(TASKS_PATH + ".Owner.update_blueprints_esi")
    def test_update_blueprints_for_owner(self, mock_update_blueprints_esi):
        tasks.update_blueprints_for_owner(self.owner.pk)
        self.assertTrue(mock_update_blueprints_esi.called)

    @patch(TASKS_PATH + ".Owner.update_blueprints_esi")
    def test_update_all_blueprints(self, mock_update_blueprints_esi):
        tasks.update_all_blueprints()
        self.assertTrue(mock_update_blueprints_esi.called)
