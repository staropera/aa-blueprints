from django.urls import path

from .views import regular_views
from .views.blueprint_list import BlueprintListJson

app_name = "blueprints"

urlpatterns = [
    path("", regular_views.index, name="index"),
    path(
        "modals/view_blueprint",
        regular_views.view_blueprint_modal,
        name="view_blueprint_modal",
    ),
    path(
        "modals/view_request",
        regular_views.view_request_modal,
        name="view_request_modal",
    ),
    path(
        "owners/add/character",
        regular_views.add_personal_blueprint_owner,
        name="add_personal_blueprint_owner",
    ),
    path(
        "owners/add/corporation",
        regular_views.add_corporate_blueprint_owner,
        name="add_corporate_blueprint_owner",
    ),
    path(
        "owners/user",
        regular_views.list_user_owners,
        name="list_user_owners",
    ),
    path(
        "owners/<int:owner_id>/remove",
        regular_views.remove_owner,
        name="remove_owner",
    ),
    path("blueprints", BlueprintListJson.as_view(), name="list_blueprints"),
    path("requests/user", regular_views.list_user_requests, name="list_user_requests"),
    path("requests/open", regular_views.list_open_requests, name="list_open_requests"),
    path("requests/add", regular_views.create_request, name="create_request"),
    path(
        "requests/<int:request_id>/open",
        regular_views.mark_request_open,
        name="request_open",
    ),
    path(
        "requests/<int:request_id>/fulfill",
        regular_views.mark_request_fulfilled,
        name="request_fulfilled",
    ),
    path(
        "requests/<int:request_id>/in_progress",
        regular_views.mark_request_in_progress,
        name="request_in_progress",
    ),
    path(
        "requests/<int:request_id>/cancel",
        regular_views.mark_request_cancelled,
        name="request_cancelled",
    ),
    path(
        "list_blueprints_ffd",
        regular_views.list_blueprints_ffd,
        name="list_blueprints_ffd",
    ),
]
