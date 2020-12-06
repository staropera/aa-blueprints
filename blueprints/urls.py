from django.urls import path

from . import views

app_name = "blueprints"

urlpatterns = [
    path("", views.index, name="index"),
    path("add_blueprint_owner", views.add_blueprint_owner, name="add_blueprint_owner"),
    path("list_data", views.list_data, name="list_data"),
]
