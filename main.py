import cv2
import cvzone
import pickle
import numpy

video = cv2.VideoCapture("carPark.mp4")

width, height = 107, 48

try:
    with open("CarParkingPosition", "rb") as file:
        parkingPositionList = pickle.load(file)
except:
    parkingPositionList = []


def checkParkingSpace():
    for position in parkingPositionList:
        x, y = position

        cropedImage = img[y : y + height, x : x + width]
        cv2.imshow(f"{position}", cropedImage)
    
    for position in parkingPositionList:
            x, y = position
    
            cv2.rectangle(
                img,
                position,
                (x + (width), y + height),
                (255, 0, 255),
                2,
            )


while True:

    if video.get(cv2.CAP_PROP_POS_FRAMES) == video.get(cv2.CAP_PROP_FRAME_COUNT):
        video.set(cv2.CAP_PROP_POS_FRAMES, 0)

    success, img = video.read()

    checkParkingSpace()

    cv2.imshow("Video", img)
    cv2.waitKey(10)
