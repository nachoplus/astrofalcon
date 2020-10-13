# run this program on the Mac to display image streams from multiple RPis
import cv2
import imagezmq
import numpy as np
import json

image_hub = imagezmq.ImageHub(open_port='tcp://localhost:5555', REQ_REP=False)


queue, image = image_hub.recv_image()
msg=json.loads(queue)
controls=msg['controls']
print(controls)

def cmd(x,key=None):
    print(key,x)

cv2.namedWindow('FalconViewer')
on_trackbar={}
for key,cn in controls.items():
    if not cn['IsWritable']:
        continue
    print(key,  cn['MinValue'], cn['MaxValue'])
    if cn['MaxValue']>=1000:
        mult=1000
    else:
        mult=1
    on_trackbar[key]=lambda x:cmd(x,key=f'{key}')
    cv2.createTrackbar(f'{key}{ mult if mult!=1 else ""}', 'FalconViewer', int(cn['MinValue']/mult), int(cn['MaxValue']/mult), on_trackbar[key])


while True:  # show streamed images until Ctrl-C
    queue, image = image_hub.recv_image()
    msg=json.loads(queue)
    if msg['image_type']=='jpg':
        img=cv2.imdecode(image,1)
    else:
        img=image
    cv2.imshow('FalconViewer', img)
    cv2.waitKey(1)

