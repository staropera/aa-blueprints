from django.contrib import admin

from .models import Blueprint, IndustryJob, Location, Owner, Request

# Register your models here.


@admin.register(Blueprint)
class BlueprintAdmin(admin.ModelAdmin):
    list_display = (
        "_type",
        "_owner",
        "material_efficiency",
        "time_efficiency",
        "_original",
    )

    list_select_related = ("eve_type", "owner")
    search_fields = ["eve_type__name"]

    def _type(self, obj):
        return obj.eve_type.name if obj.eve_type else None

    def _owner(self, obj):
        return obj.owner.name

    def _original(self, obj):
        return "No" if obj.runs and obj.runs > 0 else "Yes"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("id", "_name", "_type", "_group", "_solar_system", "updated_at")
    list_filter = (
        (
            "eve_solar_system__eve_constellation__eve_region",
            admin.RelatedOnlyFieldListFilter,
        ),
        ("eve_solar_system", admin.RelatedOnlyFieldListFilter),
        ("eve_type__eve_group", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ["name"]
    list_select_related = (
        "eve_solar_system",
        "eve_solar_system__eve_constellation__eve_region",
        "eve_type",
        "eve_type__eve_group",
    )

    def _name(self, obj):
        if obj.name:
            return obj.name
        if obj.parent and obj.parent.name:
            return "Child of " + obj.parent.name
        return None

    _name.admin_order_field = "name"

    def _solar_system(self, obj):
        return obj.eve_solar_system.name if obj.eve_solar_system else None

    _solar_system.admin_order_field = "eve_solar_system__name"

    def _type(self, obj):
        return obj.eve_type.name if obj.eve_type else None

    _type.admin_order_field = "eve_type__name"

    def _group(self, obj):
        return obj.eve_type.eve_group.name if obj.eve_type else None

    _group.admin_order_field = "eve_type__eve_group__name"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ("character", "_type", "corporation", "is_active")

    def _type(self, obj):
        return "Corporate" if obj.corporation else "Personal"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ("_type", "_requestor", "_owner", "_fulfilled_by")

    list_select_related = (
        "blueprint__eve_type",
        "requesting_user__profile__main_character",
    )
    search_fields = ["blueprint__eve_type__name"]

    def _type(self, obj):
        return obj.blueprint.eve_type.name if obj.blueprint.eve_type else None

    def _requestor(self, obj):
        return obj.requesting_user.profile.main_character.character_name

    def _owner(self, obj):
        return obj.blueprint.owner.name

    def _fulfilled_by(self, obj):
        return (
            obj.fulfulling_user.profile.main_character.character_name
            if obj.fulfulling_user
            else None
        )

    def has_add_permission(self, request):
        return False


@admin.register(IndustryJob)
class IndustryJobAdmin(admin.ModelAdmin):

    list_display = ("_blueprint", "_installer", "_activity")

    list_select_related = ("blueprint__eve_type",)
    search_fields = ["blueprint__eve_type__name"]

    def _blueprint(self, obj):
        return obj.blueprint.eve_type.name if obj.blueprint.eve_type else None

    def _installer(self, obj):
        return obj.installer.character_name

    def _activity(self, obj):
        return obj.get_activity_display()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
