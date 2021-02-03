from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.html import format_html
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST

from allianceauth.authentication.decorators import permissions_required
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger
from esi.decorators import token_required
from eveuniverse.models import EveType

from .. import __title__, tasks
from ..app_settings import (
    BLUEPRINTS_ADMIN_NOTIFICATIONS_ENABLED,
    BLUEPRINTS_DEFAULT_PAGE_LENGTH,
    BLUEPRINTS_LIST_ICON_OUTPUT_SIZE,
    BLUEPRINTS_PAGING_ENABLED,
)
from ..models import Blueprint, Owner, Request
from ..utils import LoggerAddTag, messages_plus, notify_admins

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@permissions_required("blueprints.basic_access")
def index(request):
    if request.user.has_perm("blueprints.manage_requests"):
        request_count = (
            Request.objects.all().requests_fulfillable_by_user(request.user).count()
            + Request.objects.all()
            .requests_being_fulfilled_by_user(request.user)
            .count()
        )
    else:
        request_count = None
    context = {
        "page_title": gettext_lazy(__title__),
        "data_tables_page_length": BLUEPRINTS_DEFAULT_PAGE_LENGTH,
        "data_tables_paging": BLUEPRINTS_PAGING_ENABLED,
        "request_count": request_count,
    }
    return render(request, "blueprints/index.html", context)


@login_required
@permissions_required("blueprints.add_corporate_blueprint_owner")
@token_required(
    scopes=[
        "esi-universe.read_structures.v1",
        "esi-corporations.read_blueprints.v1",
        "esi-assets.read_corporation_assets.v1",
        "esi-industry.read_corporation_jobs.v1",
    ]
)
def add_corporate_blueprint_owner(request, token):
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
                    "%(corporation)s was added as new corporate blueprint owner by %(user)s."
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


@login_required
@permissions_required("blueprints.add_personal_blueprint_owner")
@token_required(
    scopes=[
        "esi-universe.read_structures.v1",
        "esi-characters.read_blueprints.v1",
        "esi-assets.read_assets.v1",
        "esi-industry.read_character_jobs.v1",
    ]
)
def add_personal_blueprint_owner(request, token):
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

        with transaction.atomic():
            owner, _ = Owner.objects.update_or_create(
                corporation=None, character=owned_char
            )

            owner.save()

        tasks.update_blueprints_for_owner.delay(owner_pk=owner.pk)
        tasks.update_locations_for_owner.delay(owner_pk=owner.pk)
        messages_plus.info(
            request,
            format_html(
                gettext_lazy(
                    "%(character)s has been added. We have started fetching blueprints "
                    "for this character. You will receive a report once "
                    "the process is finished."
                )
                % {
                    "character": format_html(
                        "<strong>{}</strong>", owner.character.character.character_name
                    ),
                }
            ),
        )
        if BLUEPRINTS_ADMIN_NOTIFICATIONS_ENABLED:
            notify_admins(
                message=gettext_lazy(
                    "%(character)s was added as a new personal blueprint owner."
                )
                % {
                    "character": owner.character.character.character_name,
                },
                title="{}: blueprint owner added: {}".format(
                    __title__, owner.character.character.character_name
                ),
            )
    return redirect("blueprints:index")


def convert_blueprint(blueprint: Blueprint, user, details=False) -> dict:
    variant = EveType.IconVariant.BPC if blueprint.runs else EveType.IconVariant.BPO
    icon = format_html(
        '<img src="{}" width="{}" height="{}">',
        blueprint.eve_type.icon_url(size=64, variant=variant),
        BLUEPRINTS_LIST_ICON_OUTPUT_SIZE,
        BLUEPRINTS_LIST_ICON_OUTPUT_SIZE,
    )
    runs = "" if not blueprint.runs or blueprint.runs == -1 else blueprint.runs
    original = "✓" if not blueprint.runs or blueprint.runs == -1 else ""
    filter_is_original = (
        gettext_lazy("Yes")
        if not blueprint.runs or blueprint.runs == -1
        else gettext_lazy("No")
    )
    if blueprint.owner.corporation:
        owner_type = "corporation"
    else:
        owner_type = "character"

    if user.has_perm("blueprints.view_blueprint_locations"):
        location = blueprint.location.name_plus
    else:
        location = gettext_lazy("(Unknown)")
    summary = {
        "icn": icon,
        "qty": blueprint.quantity,
        "pk": blueprint.pk,
        "nme": blueprint.eve_type.name,
        "loc": location,
        "me": blueprint.material_efficiency,
        "te": blueprint.time_efficiency,
        "og": original,
        "iog": filter_is_original,
        "rns": runs,
        "on": blueprint.owner.name,
        "ot": owner_type,
        "use": blueprint.has_industryjob(),
    }
    if details:
        if blueprint.has_industryjob() and user.has_perm(
            "blueprints.view_industry_jobs"
        ):
            job = {
                "activity": blueprint.industryjob.get_activity_display(),
                "installer": blueprint.industryjob.installer.character_name,
                "runs": blueprint.industryjob.runs,
                "start_date": blueprint.industryjob.start_date,
                "end_date": blueprint.industryjob.end_date,
            }
            summary.update({"job": job})
        summary.update({"frm": blueprint.eve_type.name.endswith(" Formula")})
    return summary


"""
@login_required
@permissions_required("blueprints.basic_access")
def list_blueprints(request):
    blueprint_rows = [
        convert_blueprint(blueprint, request.user)
        for blueprint in Blueprint.objects.user_has_access(request.user)
    ]
    return JsonResponse(blueprint_rows, safe=False)
"""


@login_required
@permissions_required("blueprints.basic_access")
def list_blueprints_ffd(request):
    """filterDropDown endpoint with server-side processing for blueprints list"""
    result = dict()
    blueprint_query = Blueprint.objects.user_has_access(
        request.user
    ).annotate_owner_name()
    columns = request.GET.get("columns")
    if columns:
        for column in columns.split(","):
            if column == "location":
                if request.user.has_perm("blueprints.view_blueprint_locations"):
                    options = blueprint_query.values_list(
                        "location__name_plus", flat=True
                    )
                else:
                    options = []
            elif column == "material_efficiency":
                options = blueprint_query.values_list("material_efficiency", flat=True)
            elif column == "time_efficiency":
                options = blueprint_query.values_list("time_efficiency", flat=True)
            elif column == "owner":
                options = blueprint_query.values_list("owner_name", flat=True)
            elif column == "is_original":
                options = map(
                    lambda x: "yes" if x is None else "no",
                    blueprint_query.values_list("runs", flat=True),
                )
            else:
                options = [f"** ERROR: Invalid column name '{column}' **"]

            result[column] = sorted(list(set(options)))

    return JsonResponse(result, safe=False)


@login_required
@permissions_required(
    "blueprints.add_personal_blueprint_owner",
    "blueprints.add_corporate_blueprint_owner",
)
def list_user_owners(request):
    owners = Owner.objects.filter(character__user=request.user)
    results = []
    for owner in owners:
        if owner.corporation:
            owner_type = "corporate"
            owner_type_display = gettext_lazy("Corporate")
            owner_name = owner.corporation.corporation_name
        else:
            owner_type = "personal"
            owner_type_display = gettext_lazy("Personal")
            owner_name = owner.character.character.character_name
        results.append(
            {
                "id": owner.pk,
                "type": owner_type,
                "type_display": owner_type_display,
                "name": owner_name,
            }
        )
    return JsonResponse(results, safe=False)


@login_required
def view_blueprint_modal(request):
    blueprint = Blueprint.objects.get(pk=request.GET.get("blueprint_id"))
    context = {"blueprint": convert_blueprint(blueprint, request.user, details=True)}
    return render(request, "blueprints/modals/view_blueprint_content.html", context)


@login_required
@permissions_required(("blueprints.request_blueprints", "blueprints.manage_requests"))
def view_request_modal(request):
    user_request = Request.objects.get(pk=request.GET.get("request_id"))
    context = {"request": convert_request(user_request, request.user)}
    return render(request, "blueprints/modals/view_request_content.html", context)


@login_required
@permissions_required("blueprints.request_blueprints")
def create_request(request):
    if request.method == "POST":
        requested = Blueprint.objects.get(pk=request.POST.get("pk"))
        runs = request.POST.get("runs")
        if runs == "":
            runs = None
        user = request.user
        Request.objects.create(
            blueprint=requested,
            requesting_user=user,
            status=Request.STATUS_OPEN,
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


def convert_request(request: Request, user) -> dict:
    variant = (
        EveType.IconVariant.BPC if request.blueprint.runs else EveType.IconVariant.BPO
    )
    icon = format_html(
        '<img src="{}" width="{}" height="{}">',
        request.blueprint.eve_type.icon_url(size=64, variant=variant),
        BLUEPRINTS_LIST_ICON_OUTPUT_SIZE,
        BLUEPRINTS_LIST_ICON_OUTPUT_SIZE,
    )

    if request.blueprint.owner.corporation:
        owner_type = "corporation"
    else:
        owner_type = "character"

    if user.has_perm("blueprints.view_blueprint_locations"):
        location = request.blueprint.location.name_plus
    else:
        location = gettext_lazy("(Unknown)")

    return {
        "request_id": request.pk,
        "type_icon": icon,
        "type_name": request.blueprint.eve_type.name,
        "owner_name": request.blueprint.owner.name,
        "owner_type": owner_type,
        "requestor": request.requesting_user.profile.main_character.character_name,
        "location": location,
        "material_efficiency": request.blueprint.material_efficiency,
        "time_efficiency": request.blueprint.time_efficiency,
        "runs": request.runs if request.runs else "",
        "status": request.status,
        "status_display": request.get_status_display(),
    }


@login_required
@permissions_required("blueprints.request_blueprints")
def list_user_requests(request):

    request_rows = list()

    request_query = Request.objects.select_related_default().filter(
        requesting_user=request.user, closed_at=None
    )
    for req in request_query:
        request_rows.append(convert_request(req, request.user))

    return JsonResponse(request_rows, safe=False)


@login_required
@permissions_required("blueprints.manage_requests")
def list_open_requests(request):

    request_rows = list()

    requests = Request.objects.select_related_default().requests_fulfillable_by_user(
        request.user
    ) | Request.objects.select_related_default().requests_being_fulfilled_by_user(
        request.user
    )

    for req in requests:
        request_rows.append(convert_request(req, request.user))

    return JsonResponse(request_rows, safe=False)


def mark_request(
    request, request_id, status, fulfilling_user, closed, *, can_requestor_edit=False
):
    completed = False
    user_request = Request.objects.get(pk=request_id)

    corporation_ids = {
        character.character.corporation_id
        for character in request.user.character_ownerships.all()
    }
    character_ownership_ids = {
        character.pk for character in request.user.character_ownerships.all()
    }
    if (
        (
            user_request.blueprint.owner.corporation
            and user_request.blueprint.owner.corporation.corporation_id
            in corporation_ids
        )
        or (
            not user_request.blueprint.owner.corporation
            and user_request.blueprint.owner.character.pk in character_ownership_ids
        )
        or (can_requestor_edit and user_request.requesting_user == request.user)
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
@permissions_required("blueprints.manage_requests")
@require_POST
def mark_request_fulfilled(request, request_id):
    user_request, completed = mark_request(
        request, request_id, Request.STATUS_FULFILLED, request.user, True
    )
    if completed:
        messages_plus.info(
            request,
            format_html(
                gettext_lazy(
                    "The request for %(blueprint)s has been closed as fulfilled."
                )
                % {"blueprint": user_request.blueprint.eve_type.name}
            ),
        )
    else:
        messages_plus.error(
            request,
            format_html(
                gettext_lazy("Fulfilling the request for %(blueprint)s has failed.")
                % {"blueprint": user_request.blueprint.eve_type.name}
            ),
        )
    return redirect("blueprints:index")


@login_required
@permissions_required("blueprints.manage_requests")
@require_POST
def mark_request_in_progress(request, request_id):
    user_request, completed = mark_request(
        request, request_id, Request.STATUS_IN_PROGRESS, request.user, False
    )
    if completed:
        messages_plus.info(
            request,
            format_html(
                gettext_lazy(
                    "The request for %(blueprint)s has been marked as in progress."
                )
                % {"blueprint": user_request.blueprint.eve_type.name}
            ),
        )
    else:
        messages_plus.error(
            request,
            format_html(
                gettext_lazy(
                    "Marking the request for %(blueprint)s as in progress has failed."
                )
                % {"blueprint": user_request.blueprint.eve_type.name}
            ),
        )
    return redirect("blueprints:index")


@login_required
@permissions_required("blueprints.manage_requests")
@require_POST
def mark_request_open(request, request_id):
    user_request, completed = mark_request(
        request, request_id, Request.STATUS_OPEN, None, False
    )
    if completed:
        messages_plus.info(
            request,
            format_html(
                gettext_lazy("The request for %(blueprint)s has been re-opened.")
                % {"blueprint": user_request.blueprint.eve_type.name}
            ),
        )
    else:
        messages_plus.error(
            request,
            format_html(
                gettext_lazy("Re-opening the request for %(blueprint)s has failed.")
                % {"blueprint": user_request.blueprint.eve_type.name}
            ),
        )
    return redirect("blueprints:index")


@login_required
@permissions_required(["blueprints.basic_access", "blueprints.manage_requests"])
@require_POST
def mark_request_cancelled(request, request_id):
    user_request, completed = mark_request(
        request,
        request_id,
        Request.STATUS_CANCELLED,
        None,
        True,
        can_requestor_edit=True,
    )
    if completed:
        messages_plus.info(
            request,
            format_html(
                gettext_lazy(
                    "The request for %(blueprint)s has been closed as cancelled."
                )
                % {"blueprint": user_request.blueprint.eve_type.name}
            ),
        )
    else:
        messages_plus.error(
            request,
            format_html(
                gettext_lazy("Cancelling the request for %(blueprint)s has failed.")
                % {"blueprint": user_request.blueprint.eve_type.name}
            ),
        )
    return redirect("blueprints:index")


@login_required
@permissions_required(
    "blueprints.add_personal_blueprint_owner",
    "blueprints.add_corporate_blueprint_owner",
)
@require_POST
def remove_owner(request, owner_id):
    owner = Owner.objects.filter(pk=owner_id, character__user=request.user).first()
    completed = False
    owner_name = None

    if owner:
        owner_name = (
            owner.corporation.corporation_name
            if owner.corporation
            else owner.character.character.character_name
        )
        owner.delete()
        completed = True

    if completed:
        messages_plus.info(
            request,
            format_html(
                gettext_lazy("%(owner)s has been removed as a blueprint owner.")
                % {"owner": owner_name}
            ),
        )
    else:
        messages_plus.error(
            request,
            format_html(gettext_lazy("Removing the blueprint owner has failed.")),
        )
    return redirect("blueprints:index")
