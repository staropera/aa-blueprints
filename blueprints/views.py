from datetime import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.html import format_html
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST

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
from .models import Blueprint, Owner, Request
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
        "blueprint_id": blueprint.pk,
        "type_name": blueprint.eve_type.name,
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
def list_blueprints(request):

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


@login_required
@permission_required("blueprints.request_blueprints")
def create_request_modal(request):
    blueprint = Blueprint.objects.get(pk=request.GET.get("blueprint_id"))
    context = {"blueprint": convert_blueprint(blueprint)}
    return render(request, "blueprints/modals/create_request_content.html", context)


@login_required
@permission_required(("blueprints.request_blueprints", "blueprints.manage_requests"))
def view_request_modal(request):
    user_request = Request.objects.get(pk=request.GET.get("request_id"))
    context = {"request": convert_request(user_request)}
    return render(request, "blueprints/modals/view_request_content.html", context)


@login_required
@permission_required("blueprints.request_blueprints")
def create_request(request):
    if request.method == "POST":
        requested = Blueprint.objects.get(pk=request.POST.get("blueprint_id"))
        runs = request.POST.get("runs")
        if runs == "":
            runs = None
        user = request.user
        Request.objects.create(
            eve_type=requested.eve_type,
            requestee_corporation=requested.owner.corporation,
            requesting_user=user,
            status=Request.STATUS_OPEN,
            location=requested.location,
            material_efficiency=requested.material_efficiency,
            time_efficiency=requested.time_efficiency,
            runs=runs,
        )
        messages_plus.info(
            request,
            format_html(
                gettext_lazy("A copy of %(blueprint)s has been requested.")
                % {"blueprint": requested.eve_type.name}
            ),
        )
    return redirect("blueprints:index")


def convert_request(request: Request) -> dict:
    icon = format_html(
        '<img src="{}" width="{}" height="{}"/>',
        request.eve_type.icon_url(size=64, is_blueprint=True),
        BLUEPRINTS_LIST_ICON_OUTPUT_SIZE,
        BLUEPRINTS_LIST_ICON_OUTPUT_SIZE,
    )

    return {
        "request_id": request.pk,
        "type_icon": icon,
        "type_name": request.eve_type.name,
        "requestee": request.requestee_corporation.corporation_name,
        "requestor": request.requesting_user.profile.main_character.character_name,
        "location": request.location.name_plus,
        "material_efficiency": request.material_efficiency,
        "time_efficiency": request.time_efficiency,
        "runs": request.runs if request.runs else "",
        "status": request.status,
        "status_display": request.get_status_display(),
    }


@login_required
@permission_required("blueprints.request_blueprints")
def list_user_requests(request):

    request_rows = list()

    request_query = Request.objects.filter(requesting_user=request.user, closed_at=None)
    for request in request_query:
        request_rows.append(convert_request(request))

    return JsonResponse(request_rows, safe=False)


@login_required
@permission_required("blueprints.manage_requests")
def list_open_requests(request):

    request_rows = list()

    requests = list(Request.objects.requests_fulfillable_by_user(request.user)) + list(
        Request.objects.requests_being_fulfilled_by_user(request.user)
    )

    for request in requests:
        request_rows.append(convert_request(request))

    return JsonResponse(request_rows, safe=False)


def mark_request(request, status, fulfilling_user, closed):
    completed = False
    user_request = Request.objects.get(pk=request.POST.get("request_id"))

    corporation_ids = {
        character.character.corporation_id
        for character in request.user.character_ownerships.all()
    }
    if (
        user_request.requestee_corporation.corporation_id in corporation_ids
        and not user_request.closed_at
    ):
        if closed:
            user_request.closed_at = datetime.utcnow()
        else:
            user_request.closed_at = None
        user_request.fulfulling_user = fulfilling_user
        user_request.status = status
        user_request.save()
        completed = True
    return user_request, completed


@login_required
@permission_required("blueprints.manage_requests")
@require_POST
def mark_request_fulfilled(request):
    user_request, completed = mark_request(
        request, Request.STATUS_FULFILLED, request.user, True
    )
    if completed:
        messages_plus.info(
            request,
            format_html(
                gettext_lazy(
                    "The request for %(blueprint)s has been closed as fulfilled."
                )
                % {"blueprint": user_request.eve_type.name}
            ),
        )
    else:
        messages_plus.error(
            request,
            format_html(
                gettext_lazy("Fulfilling the request for %(blueprint)s has failed.")
                % {"blueprint": user_request.eve_type.name}
            ),
        )
    return redirect("blueprints:index")


@login_required
@permission_required("blueprints.manage_requests")
@require_POST
def mark_request_in_progress(request):
    user_request, completed = mark_request(
        request, Request.STATUS_IN_PROGRESS, request.user, False
    )
    if completed:
        messages_plus.info(
            request,
            format_html(
                gettext_lazy(
                    "The request for %(blueprint)s has been marked as in progress."
                )
                % {"blueprint": user_request.eve_type.name}
            ),
        )
    else:
        messages_plus.error(
            request,
            format_html(
                gettext_lazy(
                    "Marking the request for %(blueprint)s as in progress has failed."
                )
                % {"blueprint": user_request.eve_type.name}
            ),
        )
    return redirect("blueprints:index")


@login_required
@permission_required("blueprints.manage_requests")
@require_POST
def mark_request_open(request):
    user_request, completed = mark_request(request, Request.STATUS_OPEN, None, False)
    if completed:
        messages_plus.info(
            request,
            format_html(
                gettext_lazy("The request for %(blueprint)s has been re-opened.")
                % {"blueprint": user_request.eve_type.name}
            ),
        )
    else:
        messages_plus.error(
            request,
            format_html(
                gettext_lazy("Re-opening the request for %(blueprint)s has failed.")
                % {"blueprint": user_request.eve_type.name}
            ),
        )
    return redirect("blueprints:index")


@login_required
@permission_required(["blueprints.basic_access", "blueprints.manage_requests"])
@require_POST
def mark_request_cancelled(request):
    user_request, completed = mark_request(
        request, Request.STATUS_CANCELLED, None, True
    )
    if completed:
        messages_plus.info(
            request,
            format_html(
                gettext_lazy(
                    "The request for %(blueprint)s has been closed as cancelled."
                )
                % {"blueprint": user_request.eve_type.name}
            ),
        )
    else:
        messages_plus.error(
            request,
            format_html(
                gettext_lazy("Cancelling the request for %(blueprint)s has failed.")
                % {"blueprint": user_request.eve_type.name}
            ),
        )
    return redirect("blueprints:index")
