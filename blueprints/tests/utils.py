import random
import socket
import string
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from allianceauth.eveonline.models import EveCharacter
from esi.models import Scope, Token


def _get_random_string(char_count):
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(char_count)
    )


def _dt_eveformat(dt: object) -> str:
    """converts a datetime to a string in eve format
    e.g. '2019-06-25T19:04:44'
    """
    dt2 = datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    return dt2.isoformat()


def _generate_token(
    character_id: int,
    character_name: str,
    access_token: str = "access_token",
    refresh_token: str = "refresh_token",
    scopes: list = None,
    timestamp_dt: object = None,
    expires_in: int = 1200,
) -> dict:

    if timestamp_dt is None:
        timestamp_dt = datetime.utcnow()
    if scopes is None:
        scopes = [
            "esi-universe.read_structures.v1",
            "esi-corporations.read_blueprints.v1",
            "esi-assets.read_corporation_assets.v1",
            "esi-characters.read_blueprints.v1",
            "esi-assets.read_assets.v1",
            "esi-industry.read_character_jobs.v1",
            "esi-industry.read_corporation_jobs.v1",
        ]
    token = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "refresh_token": refresh_token,
        "timestamp": int(timestamp_dt.timestamp()),
        "CharacterID": character_id,
        "CharacterName": character_name,
        "ExpiresOn": _dt_eveformat(timestamp_dt + timedelta(seconds=expires_in)),
        "Scopes": " ".join(list(scopes)),
        "TokenType": "Character",
        "CharacterOwnerHash": _get_random_string(28),
        "IntellectualProperty": "EVE",
    }
    return token


def _store_as_Token(token: dict, user: object) -> object:
    """Stores a generated token dict as Token object for given user

    returns Token object
    """
    obj = Token.objects.create(
        access_token=token["access_token"],
        refresh_token=token["refresh_token"],
        user=user,
        character_id=token["CharacterID"],
        character_name=token["CharacterName"],
        token_type=token["TokenType"],
        character_owner_hash=token["CharacterOwnerHash"],
    )
    for scope_name in token["Scopes"].split(" "):
        scope, _ = Scope.objects.get_or_create(name=scope_name)
        obj.scopes.add(scope)

    return obj


def add_new_token(user: User, character: EveCharacter, scopes: list) -> Token:
    """generates a new Token for the given character and adds it to the user"""
    return _store_as_Token(
        _generate_token(
            character_id=character.character_id,
            character_name=character.character_name,
            scopes=scopes,
        ),
        user,
    )


class SocketAccessError(Exception):
    pass


class NoSocketsTestCase(TestCase):
    """Variation of TestCase class that prevents any use of sockets"""

    @classmethod
    def setUpClass(cls):
        cls.socket_original = socket.socket
        socket.socket = cls.guard
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        socket.socket = cls.socket_original
        return super().tearDownClass()

    @staticmethod
    def guard(*args, **kwargs):
        raise SocketAccessError("Attempted to access network")
