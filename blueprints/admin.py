from django.contrib import admin

from .models import Blueprint, Location

# Register your models here.


@admin.register(Blueprint)
class BlueprintAdmin(admin.ModelAdmin):
    pass


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
        return obj.name_plus

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
