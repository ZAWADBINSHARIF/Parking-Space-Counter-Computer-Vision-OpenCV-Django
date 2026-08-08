import cv2
import pickle

img = cv2.imread("image.png")

width, height = 107, 48

parkingPositionList = []


def mouseClick(events, x, y, flags, params):
    global deleteMode

    if events == cv2.EVENT_RBUTTONDOWN:

        for i, position in enumerate(parkingPositionList):
            x1, y1 = position

            if (
                x1 - width // 2 < x < x1 + width // 2
                and y1 - height // 2 < y < y1 + height // 2
            ):
                parkingPositionList.pop(i)
                break

    if events == cv2.EVENT_LBUTTONDOWN:
        parkingPositionList.append((x, y))


cv2.namedWindow("image")
cv2.setMouseCallback("image", mouseClick)

while True:

    # Create a fresh copy every frame
    display_img = img.copy()

    for position in parkingPositionList:
        cv2.rectangle(
            display_img,
            (position[0] - (width // 2), position[1] - (height // 2)),
            (position[0] + (width // 2), position[1] + (height // 2)),
            (255, 0, 255),
            2,
        )

    cv2.imshow("image", display_img)

    key = cv2.waitKey(1)
