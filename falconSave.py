import cv2
import imagezmq
import datetime
import json
import argparse
import logging

logging.basicConfig(format='%(asctime)s %(levelname)s:falconHTTP %(message)s',level=logging.DEBUG)

def takePicture(cameraServerIP,pic):
    image_hub = imagezmq.ImageHub(open_port=f'tcp://{cameraServerIP}:5555', REQ_REP=False)
    queue, image = image_hub.recv_image()
    msg=json.loads(queue)
    if msg['image_type']=='jpg':
        img=cv2.imdecode(image,1)
    else:
        img=image
    timestamp = datetime.datetime.now()
    text=timestamp.strftime("%Y%m%d%H%M%S")
    cameraInfo=msg['camera_info']['Name'].replace(' ','_')
    picName=f'{text}_{cameraInfo}.{pic}'
    logging.info(f"Taking {pic} frame:{picName}")
    cv2.imwrite(picName, img)
    return picName

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--cameraServerIP", type=str, default='localhost',
        help="ip address of Camera Server")
    ap.add_argument("-f", "--format", type=str, default='jpg',
        help="Picture format [jpg|png]")
    args = vars(ap.parse_args())
    logging.info(f"Connecting to:{args['cameraServerIP']}")
    picName=takePicture(args['cameraServerIP'],args['format'])
    logging.info(f"Save file:{picName}")
