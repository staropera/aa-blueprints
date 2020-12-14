from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.html import format_html
from django.utils.translation import gettext_lazy

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from esi.decorators import token_required

from . import __title__, tasks
from .app_settings import (
    BLUEPRINTS_ADMIN_NOTIFICATIONS_ENABLED,
    BLUEPRINTS_DEFAULT_PAGE_LENGTH,
    BLUEPRINTS_LIST_ICON_OUTPUT_SIZE,
    BLUEPRINTS_PAGING_ENABLED,
)
from .models import Blueprint, Owner
from .utils import messages_plus, notify_admins


@login_required
@permission_required("blueprints.basic_access")
def index(request):

    context = {
        "page_title": gettext_lazy(__title__),
        "data_tables_page_length": BLUEPRINTS_DEFAULT_PAGE_LENGTH,
        "data_tables_paging": BLUEPRINTS_PAGING_ENABLED,
    }
    return render(request, "blueprints/index.html", context)


@login_required
@permission_required("blueprints.add_blueprint_owner")
@token_required(
    scopes=[
        "esi-universe.read_structures.v1",
        "esi-corporations.read_blueprints.v1",
        "esi-assets.read_corporation_assets.v1",
    ]
)
def add_blueprint_owner(request, token):
    token_char = EveCharacter.objects.get(character_id=token.character_id)

    success = True
    try:
        owned_char = CharacterOwnership.objects.get(
            user=request.user, character=token_char
        )
    except CharacterOwnership.DoesNotExist:
        messages_plus.error(
            request,
            format_html(
                gettext_lazy(
                    "You can only use your main or alt characters "
                    "to add corporations. "
                    "However, character %s is neither. "
                )
                % format_html("<strong>{}</strong>", token_char.character_name)
            ),
        )
        success = False
        owned_char = None

    if success:
        try:
            corporation = EveCorporationInfo.objects.get(
                corporation_id=token_char.corporation_id
            )
        except EveCorporationInfo.DoesNotExist:
            corporation = EveCorporationInfo.objects.create_corporation(
                token_char.corporation_id
            )

        with transaction.atomic():
            owner, _ = Owner.objects.update_or_create(
                corporation=corporation, defaults={"character": owned_char}
            )

            owner.save()

        tasks.update_blueprints_for_owner.delay(owner_pk=owner.pk)
        tasks.update_locations_for_owner.delay(owner_pk=owner.pk)
        messages_plus.info(
            request,
            format_html(
                gettext_lazy(
                    "%(corporation)s has been added with %(character)s "
                    "as sync character. We have started fetching blueprints "
                    "for this corporation. You will receive a report once "
                    "the process is finished."
                )
                % {
                    "corporation": format_html("<strong>{}</strong>", owner),
                    "character": format_html(
                        "<strong>{}</strong>", owner.character.character.character_name
                    ),
                }
            ),
        )
        if BLUEPRINTS_ADMIN_NOTIFICATIONS_ENABLED:
            notify_admins(
                message=gettext_lazy(
                    "%(corporation)s was added as new " "blueprint owner by %(user)s."
                )
                % {
                    "corporation": owner.corporation.corporation_name,
                    "user": request.user.username,
                },
                title="{}: blueprint owner added: {}".format(
                    __title__, owner.corporation.corporation_name
                ),
            )
    return redirect("blueprints:index")


def convert_blueprint(blueprint) -> dict:
    icon = format_html(
        '<img src="{}" width="{}" height="{}"/>',
        blueprint.eve_type.icon_url(size=64, is_blueprint=True),
        BLUEPRINTS_LIST_ICON_OUTPUT_SIZE,
        BLUEPRINTS_LIST_ICON_OUTPUT_SIZE,
    )
    runs = "" if not blueprint.runs or blueprint.runs < 1 else blueprint.runs
    original = "✓" if not blueprint.runs or blueprint.runs == -1 else ""
    filter_is_original = (
        gettext_lazy("Yes")
        if not blueprint.runs or blueprint.runs == -1
        else gettext_lazy("No")
    )
    return {
        "type_icon": icon,
        "quantity": blueprint.quantity,
        "type": blueprint.eve_type.name,
        "location": blueprint.location.name_plus,
        "material_efficiency": blueprint.material_efficiency,
        "time_efficiency": blueprint.time_efficiency,
        "original": original,
        "filter_is_original": filter_is_original,
        "runs": runs,
        "owner": blueprint.owner.corporation.corporation_name,
    }


@login_required
@permission_required("blueprints.basic_access")
def list_data(request):
    """returns blueprint list in JSON for AJAX call in blueprint_list view"""

    blueprint_rows = list()
    corporation_ids = {
        character.character.corporation_id
        for character in request.user.character_ownerships.all()
    }
    corporations = list(
        EveCorporationInfo.objects.filter(corporation_id__in=corporation_ids)
    )
    if request.user.has_perm("blueprints.view_alliance_blueprints"):
        alliances = {
            corporation.alliance for corporation in corporations if corporation.alliance
        }
        for alliance in alliances:
            corporations += alliance.evecorporationinfo_set.all()

        corporations = list(set(corporations))

    blueprints_query = Blueprint.objects.filter(
        owner__corporation__in=corporations
    ).select_related()

    for blueprint in blueprints_query:
        blueprint_rows.append(convert_blueprint(blueprint))

    return JsonResponse(blueprint_rows, safe=False)
