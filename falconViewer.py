# run this program on the Mac to display image streams from multiple RPis
import cv2
import imagezmq

image_hub = imagezmq.ImageHub(open_port='tcp://localhost:5555', REQ_REP=False)
image_hub.connect('tcp://localhost:5555')

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
    cv2.imshow('Trackbars', img) # 1 window for each RPi
    l_h = cv2.getTrackbarPos('L - H', 'Trackbars')
    l_s = cv2.getTrackbarPos('L - S', 'Trackbars')
    l_v = cv2.getTrackbarPos('L - V', 'Trackbars')
    u_h = cv2.getTrackbarPos('U - H', 'Trackbars')
    u_s = cv2.getTrackbarPos('U - S', 'Trackbars')
    u_v = cv2.getTrackbarPos('U - V', 'Trackbars')
    cv2.waitKey(1)

