from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from parking.legacy import LEGACY_HEIGHT, LEGACY_WIDTH, import_legacy_slots


class Command(BaseCommand):
    help = "Import legacy parking-slot positions (pickle or JSON) into the slots table."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=None,
            help="legacy positions file (default: CarParkingPosition in the project root)",
        )
        parser.add_argument("--width", type=int, default=LEGACY_WIDTH)
        parser.add_argument("--height", type=int, default=LEGACY_HEIGHT)

    def handle(self, *args, **options):
        if options["path"]:
            path = Path(options["path"])
        else:
            path = settings.BASE_DIR / "CarParkingPosition"
            json_path = path.with_suffix(".json")
            if json_path.exists():
                path = json_path

        if not path.exists():
            raise CommandError(f"legacy positions file not found: {path}")

        created = import_legacy_slots(
            path, width=options["width"], height=options["height"]
        )
        self.stdout.write(
            self.style.SUCCESS(f"imported {created} slot(s) from {path}")
        )
