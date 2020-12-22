from typing import Tuple

from django.contrib.auth.models import User

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.tests.auth_utils import AuthUtils
from esi.models import Token

from ..models import Owner
from .utils import add_new_token


def create_owner(character_id, corporation_id):
    _, character_ownership = create_user_from_evecharacter(character_id)
    corp = (
        EveCorporationInfo.objects.get(corporation_id=corporation_id)
        if corporation_id
        else None
    )
    return Owner.objects.create(character=character_ownership, corporation=corp)


def create_user_from_evecharacter(character_id: int) -> Tuple[User, CharacterOwnership]:
    auth_character = EveCharacter.objects.get(character_id=character_id)
    user = AuthUtils.create_user(auth_character.character_name)
    user = AuthUtils.add_permission_to_user_by_name("blueprints.basic_access", user)
    user = AuthUtils.add_permission_to_user_by_name(
        "blueprints.add_corporate_blueprint_owner", user
    )
    user = AuthUtils.add_permission_to_user_by_name(
        "blueprints.add_personal_blueprint_owner", user
    )
    user = AuthUtils.add_permission_to_user_by_name("blueprints.manage_requests", user)
    character_ownership = add_character_to_user(
        user,
        auth_character,
        is_main=True,
        scopes=[
            "esi-assets.read_assets.v1",
            "esi-assets.read_corporation_assets.v1",
            "esi-characters.read_blueprints.v1",
            "esi-corporations.read_blueprints.v1",
            "esi-industry.read_character_jobs.v1",
            "esi-industry.read_corporation_jobs.v1",
            "esi-universe.read_structures.v1",
        ],
    )
    return user, character_ownership


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
