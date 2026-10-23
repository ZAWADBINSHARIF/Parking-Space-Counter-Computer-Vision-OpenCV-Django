import re

from .models import Slot


def create_slot(name, coordinates):
    return Slot.objects.create(name=name, coordinates=coordinates)


def next_slot_name():
    highest = 0
    for name in Slot.objects.values_list("name", flat=True):
        match = re.fullmatch(r"S(\d+)", name)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"S{highest + 1}"


def get_all_slots():
    return list(Slot.objects.order_by("id"))


def delete_slot(slot_id):
    slot = Slot.objects.get(pk=slot_id)
    slot.delete()


def update_slot_status(slot_id, status):
    if status not in Slot.Status.values:
        raise ValueError(f"status must be one of {sorted(Slot.Status.values)}")
    slot = Slot.objects.get(pk=slot_id)
    slot.status = status
    slot.save(update_fields=["status"])
    return slot


def bulk_update_status(updates):
    """Apply [{"id", "status"}, ...]; only rows whose status changed are written.

    Returns (matched_ids, missing_ids).
    """
    slots_by_id = Slot.objects.in_bulk([update["id"] for update in updates])
    changed = []
    for update in updates:
        slot = slots_by_id.get(update["id"])
        if slot is None or slot.status == update["status"]:
            continue
        slot.status = update["status"]
        changed.append(slot)
    if changed:
        Slot.objects.bulk_update(changed, ["status"])
    matched = [update["id"] for update in updates if update["id"] in slots_by_id]
    missing = [update["id"] for update in updates if update["id"] not in slots_by_id]
    return matched, missing
