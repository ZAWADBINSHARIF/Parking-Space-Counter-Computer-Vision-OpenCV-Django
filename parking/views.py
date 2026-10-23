import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import services
from .models import Slot


def _valid_coordinates(value):
    return (
        isinstance(value, list)
        and len(value) == 4
        and all(
            isinstance(point, list)
            and len(point) == 2
            and all(isinstance(n, (int, float)) and not isinstance(n, bool) for n in point)
            for point in value
        )
    )


def _slot_dict(slot):
    return {
        "id": slot.id,
        "name": slot.name,
        "coordinates": slot.coordinates,
        "status": slot.status,
    }


def _parse_json(request):
    try:
        return json.loads(request.body), None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, JsonResponse({"error": "invalid JSON body"}, status=400)


@csrf_exempt
def slot_collection(request):
    if request.method == "GET":
        slots = [_slot_dict(slot) for slot in services.get_all_slots()]
        return JsonResponse({"slots": slots})

    if request.method == "POST":
        payload, error = _parse_json(request)
        if error:
            return error

        name = payload.get("name")
        coordinates = payload.get("coordinates")
        if not isinstance(name, str) or not name.strip():
            return JsonResponse({"error": "name is required"}, status=400)
        if not _valid_coordinates(coordinates):
            return JsonResponse(
                {"error": "coordinates must be 4 corner points: [[x1, y1], ..., [x4, y4]]"},
                status=400,
            )

        slot = services.create_slot(name=name.strip(), coordinates=coordinates)
        return JsonResponse(_slot_dict(slot), status=201)

    return JsonResponse({"error": "method not allowed"}, status=405)


@csrf_exempt
def slot_status(request, slot_id):
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)

    payload, error = _parse_json(request)
    if error:
        return error

    status = payload.get("status")
    if status not in Slot.Status.values:
        return JsonResponse(
            {"error": f"status must be one of {sorted(Slot.Status.values)}"}, status=400
        )

    try:
        slot = services.update_slot_status(slot_id, status)
    except Slot.DoesNotExist:
        return JsonResponse({"error": "slot not found"}, status=404)
    return JsonResponse(_slot_dict(slot))


@csrf_exempt
def slot_status_bulk(request):
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)

    payload, error = _parse_json(request)
    if error:
        return error

    updates = payload.get("updates")
    if not isinstance(updates, list) or not updates:
        return JsonResponse(
            {"error": 'updates must be a non-empty list of {"id", "status"}'}, status=400
        )

    valid_statuses = set(Slot.Status.values)
    for update in updates:
        if (
            not isinstance(update, dict)
            or not isinstance(update.get("id"), int)
            or isinstance(update.get("id"), bool)
            or update.get("status") not in valid_statuses
        ):
            return JsonResponse(
                {"error": "each update needs an integer id and a valid status"}, status=400
            )

    updated, missing = services.bulk_update_status(updates)
    return JsonResponse({"updated": updated, "missing": missing})


@csrf_exempt
def slot_detail(request, slot_id):
    try:
        slot = Slot.objects.get(pk=slot_id)
    except Slot.DoesNotExist:
        return JsonResponse({"error": "slot not found"}, status=404)

    if request.method == "GET":
        return JsonResponse(_slot_dict(slot))

    if request.method == "DELETE":
        services.delete_slot(slot_id)
        return JsonResponse({"deleted": slot_id})

    return JsonResponse({"error": "method not allowed"}, status=405)
