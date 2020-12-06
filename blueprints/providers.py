from esi.clients import EsiClientProvider

from . import __version__
from .utils import get_swagger_spec_path

esi = EsiClientProvider(
    spec_file=get_swagger_spec_path(), app_info_text=f"aa-blueprints v{__version__}"
)
