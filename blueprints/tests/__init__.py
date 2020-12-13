import random
import string
from datetime import datetime, timedelta
from typing import Tuple

from django.contrib.auth.models import User

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.tests.auth_utils import AuthUtils
from esi.models import Scope, Token

from ..models import Owner


def create_owner(character_id, corporation_id):
    _, character_ownership = create_user_from_evecharacter(character_id)
    corp = EveCorporationInfo.objects.get(corporation_id=corporation_id)
    return Owner.objects.create(character=character_ownership, corporation=corp)


def create_user_from_evecharacter(character_id: int) -> Tuple[User, CharacterOwnership]:
    auth_character = EveCharacter.objects.get(character_id=character_id)
    user = AuthUtils.create_user(auth_character.character_name)
    user = AuthUtils.add_permission_to_user_by_name("blueprints.basic_access", user)
    user = AuthUtils.add_permission_to_user_by_name(
        "blueprints.add_blueprint_owner", user
    )
    character_ownership = add_character_to_user(
        user,
        auth_character,
        is_main=True,
        scopes=[
            "esi-universe.read_structures.v1",
            "esi-corporations.read_blueprints.v1",
            "esi-assets.read_corporation_assets.v1",
        ],
    )
    return user, character_ownership


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


def add_character_to_user(
    user: User,
    character: EveCharacter,
    is_main: bool = False,
    scopes: list = None,
) -> CharacterOwnership:
    if not scopes:
        scopes = "publicData"

    token = add_new_token(user, character, scopes)
    token.save()
    if is_main:
        user.profile.main_character = character
        user.profile.save()
        user.save()

    return CharacterOwnership.objects.get(user=user, character=character)


def scope_names_set(token: Token) -> set:
    return set(token.scopes.values_list("name", flat=True))
