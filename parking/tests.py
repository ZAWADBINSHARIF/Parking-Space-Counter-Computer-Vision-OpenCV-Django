import json
import os
import pickle
import tempfile

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from . import legacy, services
from .models import Slot

CORNERS = [[10, 20], [117, 20], [117, 68], [10, 68]]


class DatabaseConnectionTest(TestCase):
    def test_mysql_connection(self):
        self.assertEqual(
            connection.settings_dict["ENGINE"], "django.db.backends.mysql"
        )
        self.assertEqual(connection.vendor, "mysql")
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            self.assertEqual(cursor.fetchone()[0], 1)


class SlotModelTest(TestCase):
    def test_table_name_matches_schema(self):
        self.assertEqual(Slot._meta.db_table, "slots")

    def test_create_slot_persists(self):
        slot = services.create_slot(name="A1", coordinates=CORNERS)
        self.assertIsNotNone(slot.id)
        self.assertEqual(slot.status, Slot.Status.OPEN)

        stored = Slot.objects.get(pk=slot.id)
        self.assertEqual(stored.name, "A1")
        self.assertEqual(stored.coordinates, CORNERS)

    def test_orm_status_update(self):
        slot = services.create_slot(name="A2", coordinates=CORNERS)
        services.update_slot_status(slot.id, Slot.Status.BOOKED)
        self.assertEqual(Slot.objects.get(pk=slot.id).status, "booked")

    def test_orm_status_update_rejects_invalid_status(self):
        slot = services.create_slot(name="A3", coordinates=CORNERS)
        with self.assertRaises(ValueError):
            services.update_slot_status(slot.id, "occupied")

    def test_next_slot_name_auto_increments(self):
        self.assertEqual(services.next_slot_name(), "S1")
        services.create_slot(name="S1", coordinates=CORNERS)
        services.create_slot(name="A1", coordinates=CORNERS)  # non-S names ignored
        self.assertEqual(services.next_slot_name(), "S2")
        services.create_slot(name="S10", coordinates=CORNERS)
        self.assertEqual(services.next_slot_name(), "S11")


class SlotApiTest(TestCase):
    def _create(self, name="A1", coordinates=CORNERS):
        return self.client.post(
            "/api/slots/",
            data=json.dumps({"name": name, "coordinates": coordinates}),
            content_type="application/json",
        )

    def test_create_slot_via_api(self):
        response = self._create()
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "A1")
        self.assertEqual(data["coordinates"], CORNERS)
        self.assertEqual(data["status"], "open")
        self.assertEqual(Slot.objects.count(), 1)

    def test_create_slot_rejects_bad_coordinates(self):
        bad_payloads = [
            [[1, 2], [3, 4]],
            "not-coords",
            [[1, 2], [3, 4], [5, 6], [7, "x"]],
        ]
        for bad in bad_payloads:
            response = self._create(coordinates=bad)
            self.assertEqual(response.status_code, 400)
        self.assertEqual(Slot.objects.count(), 0)

    def test_list_slots(self):
        services.create_slot(name="A1", coordinates=CORNERS)
        services.create_slot(name="A2", coordinates=CORNERS)
        response = self.client.get("/api/slots/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["slots"]), 2)

    def test_status_update_simulating_opencv_result(self):
        slot = services.create_slot(name="A1", coordinates=CORNERS)

        # Simulated OpenCV result: pixel count >= 1000 -> space occupied
        response = self.client.post(
            f"/api/slots/{slot.id}/status/",
            data=json.dumps({"status": "booked"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "booked")

        # Next frame: pixel count < 1000 -> space free again
        response = self.client.post(
            f"/api/slots/{slot.id}/status/",
            data=json.dumps({"status": "open"}),
            content_type="application/json",
        )
        self.assertEqual(Slot.objects.get(pk=slot.id).status, "open")

    def test_status_update_rejects_invalid_status_and_missing_slot(self):
        slot = services.create_slot(name="A1", coordinates=CORNERS)
        response = self.client.post(
            f"/api/slots/{slot.id}/status/",
            data=json.dumps({"status": "occupied"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            "/api/slots/9999/status/",
            data=json.dumps({"status": "booked"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_bulk_status_update_from_cv_frame(self):
        slots = [
            services.create_slot(name=f"A{i}", coordinates=CORNERS) for i in range(3)
        ]
        updates = [
            {"id": slots[0].id, "status": "booked"},
            {"id": slots[1].id, "status": "booked"},
            {"id": slots[2].id, "status": "open"},
        ]
        response = self.client.post(
            "/api/slots/status/",
            data=json.dumps({"updates": updates}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["updated"], [slot.id for slot in slots])
        self.assertEqual(
            list(Slot.objects.order_by("id").values_list("status", flat=True)),
            ["booked", "booked", "open"],
        )

    def test_bulk_update_reports_missing_ids(self):
        response = self.client.post(
            "/api/slots/status/",
            data=json.dumps({"updates": [{"id": 4242, "status": "open"}]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["missing"], [4242])


class SlotDeleteTest(TestCase):
    def test_delete_slot_service(self):
        slot = services.create_slot(name="A1", coordinates=CORNERS)
        services.delete_slot(slot.id)
        self.assertEqual(Slot.objects.count(), 0)
        with self.assertRaises(Slot.DoesNotExist):
            services.delete_slot(slot.id)

    def test_get_and_delete_slot_via_api(self):
        slot = services.create_slot(name="A1", coordinates=CORNERS)

        response = self.client.get(f"/api/slots/{slot.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "A1")

        response = self.client.delete(f"/api/slots/{slot.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["deleted"], slot.id)
        self.assertEqual(Slot.objects.count(), 0)

        self.assertEqual(self.client.get(f"/api/slots/{slot.id}/").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/slots/{slot.id}/").status_code, 404)


class BulkUpdateOptimizationTest(TestCase):
    def test_unchanged_status_writes_nothing(self):
        slot = services.create_slot(name="A1", coordinates=CORNERS)
        with CaptureQueriesContext(connection) as ctx:
            services.bulk_update_status([{"id": slot.id, "status": "open"}])
        self.assertEqual(len(ctx.captured_queries), 1)  # SELECT only

        with CaptureQueriesContext(connection) as ctx:
            services.bulk_update_status([{"id": slot.id, "status": "booked"}])
        self.assertEqual(len(ctx.captured_queries), 2)  # SELECT + UPDATE


class LegacyImportTest(TestCase):
    def _temp_file(self, suffix):
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        self.addCleanup(os.unlink, path)
        return path

    def _write_pickle(self, positions):
        path = self._temp_file(".pkl")
        with open(path, "wb") as file:
            pickle.dump(positions, file)
        return path

    def _write_json(self, data):
        path = self._temp_file(".json")
        with open(path, "w") as file:
            json.dump(data, file)
        return path

    def test_load_legacy_positions_pickle(self):
        path = self._write_pickle([(10, 20), (30, 40)])
        self.assertEqual(legacy.load_legacy_positions(path), [(10, 20), (30, 40)])

    def test_load_legacy_positions_json(self):
        path = self._write_json([[1, 2], {"x": 3, "y": 4}])
        self.assertEqual(legacy.load_legacy_positions(path), [(1, 2), (3, 4)])

    def test_slot_entries_converts_top_left_to_corners(self):
        entries = legacy.slot_entries([(10, 20)], width=100, height=50)
        self.assertEqual(
            entries,
            [{"name": "S1", "coordinates": [[10, 20], [110, 20], [110, 70], [10, 70]]}],
        )

    def test_import_creates_slots_and_is_idempotent(self):
        path = self._write_pickle([(10, 20), (30, 40)])
        self.assertEqual(legacy.import_legacy_slots(path), 2)
        self.assertEqual(legacy.import_legacy_slots(path), 0)

        slots = list(Slot.objects.order_by("id"))
        self.assertEqual([slot.name for slot in slots], ["S1", "S2"])
        self.assertEqual(
            slots[0].coordinates, [[10, 20], [117, 20], [117, 68], [10, 68]]
        )
        self.assertTrue(all(slot.status == "open" for slot in slots))

    def test_management_command_imports(self):
        path = self._write_pickle([(5, 5)])
        call_command("import_legacy_slots", path=path)
        slot = Slot.objects.get()
        self.assertEqual(slot.name, "S1")
        self.assertEqual(slot.coordinates, [[5, 5], [112, 5], [112, 53], [5, 53]])
