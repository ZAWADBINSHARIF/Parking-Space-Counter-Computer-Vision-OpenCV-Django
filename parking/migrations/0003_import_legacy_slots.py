# Seeds the slots table from the legacy CarParkingPosition file (pickle or JSON).
# Skips test databases so `manage.py test` stays deterministic.
import os

from django.conf import settings
from django.db import migrations


def import_legacy_slots(apps, schema_editor):
    db_name = schema_editor.connection.settings_dict["NAME"] or ""
    if os.path.basename(db_name).startswith("test"):
        return

    from parking.legacy import import_legacy_slots as do_import

    for filename in ("CarParkingPosition.json", "CarParkingPosition"):
        path = settings.BASE_DIR / filename
        if path.exists():
            do_import(path)
            return


class Migration(migrations.Migration):

    dependencies = [
        ("parking", "0002_alter_slot_id"),
    ]

    operations = [
        migrations.RunPython(import_legacy_slots, migrations.RunPython.noop),
    ]
