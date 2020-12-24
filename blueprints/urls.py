from django.urls import path

from . import views

app_name = "blueprints"

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "modals/view_blueprint", views.view_blueprint_modal, name="view_blueprint_modal"
    ),
    path("modals/view_request", views.view_request_modal, name="view_request_modal"),
    path(
        "owners/add/character",
        views.add_personal_blueprint_owner,
        name="add_personal_blueprint_owner",
    ),
    path(
        "owners/add/corporation",
        views.add_corporate_blueprint_owner,
        name="add_corporate_blueprint_owner",
    ),
    path(
        "owners/user",
        views.list_user_owners,
        name="list_user_owners",
    ),
    path(
        "owners/<int:owner_id>/remove",
        views.remove_owner,
        name="remove_owner",
    ),
    path("blueprints", views.list_blueprints, name="list_blueprints"),
    path("requests/user", views.list_user_requests, name="list_user_requests"),
    path("requests/open", views.list_open_requests, name="list_open_requests"),
    path("requests/add", views.create_request, name="create_request"),
    path(
        "requests/<int:request_id>/open", views.mark_request_open, name="request_open"
    ),
    path(
        "requests/<int:request_id>/fulfill",
        views.mark_request_fulfilled,
        name="request_fulfilled",
    ),
    path(
        "requests/<int:request_id>/in_progress",
        views.mark_request_in_progress,
        name="request_in_progress",
    ),
    path(
        "requests/<int:request_id>/cancel",
        views.mark_request_cancelled,
        name="request_cancelled",
    ),
]
