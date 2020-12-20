# flake8: noqa
"""scripts generates large amount of blueprints for load testing

This script can be executed directly from shell.
Please make sure to set your user ID via environment variable: BLUEPRINTS_USER_ID
"""

import inspect
import os
import sys

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
myauth_dir = (
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(currentdir))))
    + "/myauth"
)
sys.path.insert(0, myauth_dir)

import django
from django.apps import apps
from django.db import transaction
from django.utils.timezone import now

# init and setup django project
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myauth.settings.local")
django.setup()

if not apps.is_installed("blueprints"):
    raise RuntimeError("The app blueprints is not installed")

"""SCRIPT"""
from random import randint

from django.contrib.auth.models import User

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.tests.auth_utils import AuthUtils
from eveuniverse.models import EveSolarSystem, EveType

from blueprints.models import Blueprint, EveSolarSystem, EveType, Location, Owner

MAX_ITEMS = 10000
OWNER_USER_ID = os.environ.get("BLUEPRINTS_USER_ID")
if not OWNER_USER_ID:
    print("Environment variable BLUEPRINTS_USER_ID is not set")
    exit(1)

user = User.objects.get(id=OWNER_USER_ID)
main_character = user.profile.main_character
character_ownership = CharacterOwnership.objects.get(
    user=user, character=main_character
)
try:
    corporation = EveCorporationInfo.objects.get(
        corporation_id=main_character.corporation_id
    )
except EveCorporationInfo.DoesNotExist:
    corporation = EveCorporationInfo.objects.create_corporation(
        main_character.corporation_id
    )

owner, _ = Owner.objects.update_or_create(
    corporation=corporation, character=character_ownership
)

# create blueprints for owner
eve_type, _ = EveType.objects.get_or_create_esi(id=692)  # stabber bp
location, _ = Location.objects.get_or_create_esi(
    id=60003760, token=owner.token()
)  # jita 4-4

print(f"Generating {MAX_ITEMS} blueprints for {corporation}...")
blueprints = [
    Blueprint(
        item_id=randint(1_000_000_000_000, 1_999_999_999_999),
        owner=owner,
        eve_type=eve_type,
        location=location,
        location_flag="CorpDeliveries",
        quantity=1,
        runs=10,
        material_efficiency=10,
        time_efficiency=20,
    )
    for _ in range(MAX_ITEMS)
]
Blueprint.objects.bulk_create(blueprints, batch_size=500, ignore_conflicts=True)

print("DONE")
