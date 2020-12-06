from django.apps import AppConfig

from . import __version__


class BlueprintsConfig(AppConfig):
    name = "blueprints"
    label = "blueprints"
    verbose_name = f"Blueprints v{__version__}"
