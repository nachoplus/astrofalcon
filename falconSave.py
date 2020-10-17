import cv2
import imagezmq
import datetime
import json
import argparse
import logging

logging.basicConfig(format='%(asctime)s %(levelname)s:falconHTTP %(message)s',level=logging.DEBUG)

def takePicture(cameraServerIP,numFrames,pic):
    image_hub = imagezmq.ImageHub(open_port=f'tcp://{cameraServerIP}:5555', REQ_REP=False)

    FIRST=True
    f=0.80
    for i in range(numFrames):  # show streamed images until Ctrl-C
        queue, image = image_hub.recv_image()
        msg=json.loads(queue)
        logging.debug(f'{i} of {numFrames} times_interval:{msg["times_interval"]}')

        if msg['image_type']=='jpg':
            img=cv2.imdecode(image,1)
        else:
            img=image

        if FIRST:
            accumulated=img
            FIRST=False
        else:
            accumulated=cv2.addWeighted(accumulated,f,img,1-f,0)


    timestamp = datetime.datetime.now()
    text=timestamp.strftime("%Y%m%d%H%M%S")
    cameraInfo=msg['camera_info']['Name'].replace(' ','_')
    picName=f'{text}_{cameraInfo}.{pic}'
    logging.info(f"Taking {pic} frame:{picName}")
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    result, encimg = cv2.imencode('.jpg', accumulated, encode_param)
    #cv2.namedWindow('FalconSave')
    #cv2.imshow('FalconSave', accumulated) 
    #cv2.waitKey()
    print(cv2.imwrite(picName, accumulated))
    return picName

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--cameraServerIP", type=str, default='localhost',
        help="ip address of Camera Server")
    ap.add_argument("-n", "--numFrames", type=int, default=10,
        help="Average numFrames")
    ap.add_argument("-f", "--format", type=str, default='jpg',
        help="Picture format [jpg|png|tiff]")
    args = vars(ap.parse_args())
    logging.info(f"Connecting to:{args['cameraServerIP']}")
    logging.info(f"Averaging {args['numFrames']} frames")
    picName=takePicture(args['cameraServerIP'],args['numFrames'],args['format'])
    logging.info(f"Save file:{picName}")
