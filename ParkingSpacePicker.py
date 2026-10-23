import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

import cv2

from parking import services

img = cv2.imread("image.png")

width, height = 107, 48

slots = []


def refreshSlots():
    global slots
    slots = services.get_all_slots()


def mouseClick(events, x, y, flags, params):

    if events == cv2.EVENT_RBUTTONDOWN:

        for slot in slots:
            x1, y1 = (int(v) for v in slot.coordinates[0])

            if x1 < x < x1 + width and y1 < y < y1 + height:
                services.delete_slot(slot.id)
                refreshSlots()
                break

    if events == cv2.EVENT_LBUTTONDOWN:
        services.create_slot(
            name=services.next_slot_name(),
            coordinates=[
                [x, y],
                [x + width, y],
                [x + width, y + height],
                [x, y + height],
            ],
        )
        refreshSlots()


cv2.namedWindow("image")
cv2.setMouseCallback("image", mouseClick)
refreshSlots()

while True:

    # Create a fresh copy every frame
    display_img = img.copy()

    for slot in slots:
        x1, y1 = (int(v) for v in slot.coordinates[0])
        cv2.rectangle(
            display_img,
            (x1, y1),
            (x1 + width, y1 + height),
            (255, 0, 255),
            2,
        )
        cv2.putText(
            display_img,
            slot.name,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 0, 255),
            1,
        )

    cv2.imshow("image", display_img)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
