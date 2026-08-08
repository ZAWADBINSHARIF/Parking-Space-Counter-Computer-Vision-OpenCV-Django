import cv2
import cvzone
import pickle
import numpy as np

video = cv2.VideoCapture("carPark.mp4")

width, height = 107, 48

try:
    with open("CarParkingPosition", "rb") as file:
        parkingPositionList = pickle.load(file)
except:
    parkingPositionList = []


def checkParkingSpace(ProcessedImage):

    spaceCounter = 0

    for position in parkingPositionList:
        x, y = position

        cropedImage = ProcessedImage[y : y + height - 5, x : x + width]
        count = cv2.countNonZero(cropedImage)
        cvzone.putTextRect(img, str(count), (x, y + height), 1, 2, offset=0)

        if count < 1000:
            color = (0, 255, 0)  # * BGR
            thickness = 5
            spaceCounter += 1
        else:
            color = (0, 0, 255)
            thickness = 2

        cv2.rectangle(img, position, (x + (width), y + height), color, thickness)

    cvzone.putTextRect(
        img,
        f"free: {str(spaceCounter)}/{len(parkingPositionList)}",
        (100, 50),
        3,
        5,
        offset=20,
        colorR=(0, 255, 0),
    )


while True:

    if video.get(cv2.CAP_PROP_POS_FRAMES) == video.get(cv2.CAP_PROP_FRAME_COUNT):
        video.set(cv2.CAP_PROP_POS_FRAMES, 0)

    success, img = video.read()

    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    imgBlur = cv2.GaussianBlur(imgGray, (3, 3), 1)

    imgThreshold = cv2.adaptiveThreshold(
        imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 16
    )

    imgThresholdInv = cv2.adaptiveThreshold(
        imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16
    )

    kernal = np.ones((3, 3), np.uint8)
    imageDilate = cv2.dilate(imgThresholdInv, kernal, iterations=1)

    checkParkingSpace(imageDilate)

    cv2.imshow("Video Blur", imgBlur)
    cv2.imshow("Video Threshold", imgThreshold)
    cv2.imshow("Video Threshold Inverse", imgThresholdInv)
    cv2.imshow("Video Dilate", imageDilate)
    cv2.imshow("Video", img)
    cv2.waitKey(10)
