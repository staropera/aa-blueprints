from django.core.management.base import BaseCommand

from ...tasks import update_all_blueprints, update_all_locations


class Command(BaseCommand):
    help = "Refreshes all blueprints and locations"

    def handle(self, *args, **options):
        update_all_blueprints.delay()
        update_all_locations.delay()
        self.stdout.write("Blueprint and location refresh tasks enqueued.")
