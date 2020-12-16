from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_material_efficiency(value):
    if value > 10 or value < 0:
        raise ValidationError(
            _("%(value)s is not a valid material efficiency"),
            params={"value": value},
        )


def validate_time_efficiency(value):
    if value % 2 != 0 or value > 20 or value < 0:
        raise ValidationError(
            _("%(value)s is not a valid time efficiency"),
            params={"value": value},
        )
