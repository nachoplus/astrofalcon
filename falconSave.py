import cv2
import imageTransport
import datetime
import json
import argparse
import logging
import numpy as np
import astropy.io.fits as pyfits
import falconHelper

logging.basicConfig(format='%(asctime)s %(levelname)s:falconSave %(message)s',level=logging.DEBUG)

def takePicture(cameraServerIP,numFrames,format):

    image_hub = imageTransport.ImageHub(open_port=f'tcp://{cameraServerIP}:5555', REQ_REP=False)

    FIRST=True
    f=1-1/numFrames
    logging.info(f"factor:{f}")
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
            imageStack=[]
            FIRST=False
        else:
                if False:
                        accumulated=cv2.addWeighted(accumulated,f,img,1-f,0)
                else:
                        accumulated=falconHelper.average(img,imageStack,n=numFrames)  


    timestamp = datetime.datetime.now()
    text=timestamp.strftime("%Y%m%d%H%M%S")
    cameraInfo=msg['camera_info']['Name'].replace(' ','_')
    picName=f'{text}_{cameraInfo}.{format}'
    logging.info(f"Taking {format} frame:{picName}")

    if format.lower() in ['jpg','jpeg','png','tiff']:
        if format in 'jpg':
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            result, encimg = cv2.imencode('.jpg', accumulated, encode_param)
        else:
            encimg=accumulated
        cv2.imwrite(picName, encimg)

    if format.lower() in ['fit','fits']:
        if len(img.shape)>2:
            img = np.swapaxes(accumulated, 0, 2)
            img = np.swapaxes(img, 1, 2)
        hdu = pyfits.PrimaryHDU(img/img.max())
        '''
        hdu.header['CAMERA']=msg['camera_info']
        hdu.header['GAIN']=gain
        hdu.header['EXPOSURE']=float(exp/1000.)
        hdu.header['CCD-TEMP']=float(self.get_temp())
        '''
        hdu.header['OWNER']="NACHO MAS"
        hdu.writeto(picName)

    if False:
        cv2.namedWindow('FalconSave')
        cv2.imshow('FalconSave', accumulated) 
        cv2.waitKey()
    
    return picName

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--cameraServerIP", type=str, default='localhost',
        help="ip address of Camera Server")
    ap.add_argument("-n", "--numFrames", type=int, default=10,
        help="Average numFrames")
    ap.add_argument("-f", "--format", type=str, default='jpg',
        help="Picture format [jpg|png|fit|tiff]")
    args = vars(ap.parse_args())

    logging.info(f"Connecting to:{args['cameraServerIP']}")
    logging.info(f"Averaging {args['numFrames']} frames")
    picName=takePicture(args['cameraServerIP'],args['numFrames'],args['format'])
    logging.info(f"Save file:{picName}")


