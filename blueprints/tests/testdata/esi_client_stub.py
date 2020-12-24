import inspect
import json
import os

from .esi_test_tools import EsiClientStub, EsiEndpoint

_currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
_FILENAME_ESI_TESTDATA = "esi_testdata.json"


def load_test_data():
    with open(f"{_currentdir}/{_FILENAME_ESI_TESTDATA}", "r", encoding="utf-8") as f:
        return json.load(f)


_endpoints = [
    EsiEndpoint(
        "Assets",
        "get_characters_character_id_assets",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Assets",
        "post_characters_character_id_assets_names",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Assets",
        "get_corporations_corporation_id_assets",
        "corporation_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Character",
        "get_characters_character_id_blueprints",
        "character_id",
    ),
    EsiEndpoint(
        "Character",
        "get_characters_character_id_corporationhistory",
        "character_id",
    ),
    EsiEndpoint(
        "Character",
        "get_characters_character_id",
        "character_id",
    ),
    EsiEndpoint(
        "Contacts",
        "get_characters_character_id_contacts",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Contacts",
        "get_characters_character_id_contacts_labels",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Contracts",
        "get_characters_character_id_contracts",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Contracts",
        "get_characters_character_id_contracts_contract_id_bids",
        ("character_id", "contract_id"),
        needs_token=True,
    ),
    EsiEndpoint(
        "Contracts",
        "get_characters_character_id_contracts_contract_id_items",
        ("character_id", "contract_id"),
        needs_token=True,
    ),
    EsiEndpoint(
        "Clones",
        "get_characters_character_id_clones",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Clones",
        "get_characters_character_id_implants",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Corporation",
        "get_corporations_corporation_id_blueprints",
        "corporation_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Industry",
        "get_characters_character_id_industry_jobs",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Industry",
        "get_corporations_corporation_id_industry_jobs",
        "corporation_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Location",
        "get_characters_character_id_location",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Location",
        "get_characters_character_id_online",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Loyalty",
        "get_characters_character_id_loyalty_points",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Mail", "get_characters_character_id_mail", "character_id", needs_token=True
    ),
    EsiEndpoint(
        "Mail",
        "get_characters_character_id_mail_lists",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Mail",
        "get_characters_character_id_mail_labels",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Mail",
        "get_characters_character_id_mail_mail_id",
        "mail_id",
        needs_token=True,
    ),
    EsiEndpoint("Market", "get_markets_prices"),
    EsiEndpoint(
        "Skills",
        "get_characters_character_id_skills",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Skills",
        "get_characters_character_id_skillqueue",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint("Status", "get_status"),
    EsiEndpoint("Universe", "get_universe_stations_station_id", "station_id"),
    EsiEndpoint("Universe", "get_universe_types_type_id", "type_id"),
    EsiEndpoint(
        "Universe",
        "get_universe_structures_structure_id",
        "structure_id",
        needs_token=True,
    ),
    EsiEndpoint("Universe", "get_universe_systems_system_id", "system_id"),
    EsiEndpoint(
        "Wallet",
        "get_characters_character_id_wallet",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Wallet",
        "get_characters_character_id_wallet_journal",
        "character_id",
        needs_token=True,
    ),
]

esi_client_stub = EsiClientStub(load_test_data(), endpoints=_endpoints)
esi_client_error_stub = EsiClientStub(
    load_test_data(), endpoints=_endpoints, http_error=True
)
