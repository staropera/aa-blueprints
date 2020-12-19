from django.test import TestCase

from esi.errors import TokenError
from esi.models import Token

from ..decorators import fetch_token_for_owner
from . import create_owner, scope_names_set
from .testdata.load_entities import load_entities

DUMMY_URL = "http://www.example.com"


class TestFetchToken(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_entities()

    def setUp(self) -> None:
        self.owner = create_owner(character_id=1101, corporation_id=2101)

    def test_specified_scope(self):
        @fetch_token_for_owner("esi-corporations.read_blueprints.v1")
        def dummy(owner, token):
            self.assertIsInstance(token, Token)
            self.assertIn("esi-corporations.read_blueprints.v1", scope_names_set(token))

        dummy(self.owner)

    def test_exceptions_if_not_found(self):
        @fetch_token_for_owner("invalid_scope")
        def dummy(owner, token):
            pass

        with self.assertRaises(TokenError):
            dummy(self.owner)
