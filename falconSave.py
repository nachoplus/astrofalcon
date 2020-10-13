# run this program on the Mac to display image streams from multiple RPis
import cv2
import imagezmq
import datetime

image_hub = imagezmq.ImageHub(open_port='tcp://localhost:5555', REQ_REP=False)
image_hub.connect('tcp://localhost:5555')


queue, image = image_hub.recv_image()
if queue=='resizedJPG':
        img=cv2.imdecode(image,1)
else:
        img=image
timestamp = datetime.datetime.now()
text=timestamp.strftime("%Y%m%d%H%M%S")
cv2.imwrite(f'{text}_{queue}.jpg', img)
cv2.imwrite(f'{text}_{queue}.png', img)
