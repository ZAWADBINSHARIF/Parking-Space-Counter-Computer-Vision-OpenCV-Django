import cv2
import pickle

img = cv2.imread("image.png")

width, height = 107, 48


try:
    with open("CarParkingPosition", "rb") as file:
        parkingPositionList = pickle.load(file)
except:
    parkingPositionList = []

print(parkingPositionList)


def mouseClick(events, x, y, flags, params):

    if events == cv2.EVENT_RBUTTONDOWN:

        for i, position in enumerate(parkingPositionList):
            x1, y1 = position

            if x1 < x < x1 + width and y1 < y < y1 + height:
                parkingPositionList.pop(i)
                break

    if events == cv2.EVENT_LBUTTONDOWN:
        parkingPositionList.append((x, y))

    with open("CarParkingPosition", "wb") as file:
        pickle.dump(parkingPositionList, file)


cv2.namedWindow("image")
cv2.setMouseCallback("image", mouseClick)

while True:

    # Create a fresh copy every frame
    display_img = img.copy()

    for position in parkingPositionList:
        cv2.rectangle(
            display_img,
            position,
            (position[0] + (width), position[1] + height),
            (255, 0, 255),
            2,
        )

    cv2.imshow("image", display_img)

    key = cv2.waitKey(1)
