# run this program on the Mac to display image streams from multiple RPis
import cv2
import imagezmq
import numpy as np

image_hub = imagezmq.ImageHub(open_port='tcp://rogueone:5555', REQ_REP=False)
image_hub.connect('tcp://localhost:5555')
bg=None

def nothing(x):
    pass

cv2.namedWindow('Trackbars')
cv2.createTrackbar('L - H', 'Trackbars', 0, 179, nothing)
cv2.createTrackbar('L - S', 'Trackbars', 0, 255, nothing)
cv2.createTrackbar('L - V', 'Trackbars', 0, 255, nothing)
cv2.createTrackbar('U - H', 'Trackbars', 179, 179, nothing)
cv2.createTrackbar('U - S', 'Trackbars', 255, 255, nothing)
cv2.createTrackbar('U - V', 'Trackbars', 255, 255, nothing)

while True:  # show streamed images until Ctrl-C
    queue, image = image_hub.recv_image()
    if queue=='resizedJPG':
        img=cv2.imdecode(image,1)
    else:
        img=image
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imshow('gray', gray) # 1 window for each RPi
    # if the background model is None, initialize it
    if bg is None:
       bg = np.zeros((img.shape[0], img.shape[1], 1), dtype = "float")
       cv2.imshow('bg0', bg) # 1 window for each RPi
    else:
       bg= cv2.accumulateWeighted(gray, bg, .5)
       print("P")
    cv2.imshow('Trackbars', img) # 1 window for each RPi
    cv2.imshow('bg', bg) # 1 window for each RPi
    l_h = cv2.getTrackbarPos('L - H', 'Trackbars')
    l_s = cv2.getTrackbarPos('L - S', 'Trackbars')
    l_v = cv2.getTrackbarPos('L - V', 'Trackbars')
    u_h = cv2.getTrackbarPos('U - H', 'Trackbars')
    u_s = cv2.getTrackbarPos('U - S', 'Trackbars')
    u_v = cv2.getTrackbarPos('U - V', 'Trackbars')
    cv2.waitKey(1)

