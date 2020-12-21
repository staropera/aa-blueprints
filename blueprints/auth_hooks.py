from django.utils.translation import ugettext_lazy as _

from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook

from . import urls
from .models import Request


class BlueprintLibraryMenuItem(MenuItemHook):
    """ This class ensures only authorized users will see the menu entry """

    def __init__(self):
        # setup menu entry for sidebar
        MenuItemHook.__init__(
            self,
            _("Blueprint Library"),
            "fas fa-scroll fa-fw",
            "blueprints:index",
            navactive=["blueprints:index"],
        )

    def render(self, request):
        if request.user.has_perm("blueprints.basic_access"):
            if request.user.has_perm("blueprints.manage_requests"):
                app_count = (
                    Request.objects.all()
                    .requests_fulfillable_by_user(request.user)
                    .count()
                    + Request.objects.all()
                    .requests_being_fulfilled_by_user(request.user)
                    .count()
                )
            else:
                app_count = None
            self.count = app_count if app_count and app_count > 0 else None
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_menu():
    return BlueprintLibraryMenuItem()


@hooks.register("url_hook")
def register_urls():
    return UrlHook(urls, "blueprints", r"^blueprints/")
