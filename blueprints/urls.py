from django.urls import path

from . import views

app_name = "blueprints"

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "modals/create_request", views.create_request_modal, name="create_request_modal"
    ),
    path("modals/view_request", views.view_request_modal, name="view_request_modal"),
    path("owner/add", views.add_blueprint_owner, name="add_blueprint_owner"),
    path("blueprints", views.list_blueprints, name="list_blueprints"),
    path("requests/user", views.list_user_requests, name="list_user_requests"),
    path("requests/open", views.list_open_requests, name="list_open_requests"),
    path("requests/add", views.create_request, name="create_request"),
    path("requests/request/open", views.mark_request_open, name="request_open"),
    path(
        "requests/request/fulfill",
        views.mark_request_fulfilled,
        name="request_fulfilled",
    ),
    path(
        "requests/request/in_progress",
        views.mark_request_in_progress,
        name="request_in_progress",
    ),
    path(
        "requests/request/cancel",
        views.mark_request_cancelled,
        name="request_cancelled",
    ),
]
