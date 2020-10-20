# run this program on the Mac to display image streams from multiple RPis
import cv2
import imageTransport
import zmq
import numpy as np
import json
from functools import partial
import argparse
import logging
import threading
import falconBase

logging.basicConfig(format='%(asctime)s %(levelname)s:falconViewer %(message)s',level=logging.INFO)


class falconViewer(falconBase.falconBase):
    def __init__(self,cameraServerIP):
        logging.info("Starting falcon Camara Viewer")
        super().__init__(cameraServerIP)       

    def update(self):
        if not self.msg is None:
            self.set_trackbars()
        threading.Timer(.10, self.update).start()



    def set_trackbars(self):
        self.control_values=self.msg['controls_values']
        values=self.control_values
        for key,cn in self.controls.items():
            if cv2.getTrackbarPos(f'{key}', 'FalconControls')!=values[key]:
                cv2.setTrackbarPos(f'{key}', 'FalconControls', values[key]) 

    def cb(self,key,x):
        cn=self.controls[key]
        if False:
            if cn['MaxValue']>=1000:
                mult=1000
            else:
                mult=1
        else:
            mult=1

        ControlType=cn['ControlType']
        d=dict()
        d={'set_control_value':{ControlType:x*mult}}   
        logging.info(f'Sending {d}')
        self.CmdSocket.send_string(json.dumps(d))
        reply = self.CmdSocket.recv()
        logging.info(reply)

    def run(self):
        cv2.namedWindow('FalconViewer')
        cv2.namedWindow('FalconControls',cv2.WINDOW_NORMAL)
        for key,cn in self.controls.items():
            if not cn['IsWritable']:
                continue
            print(key,  cn['MinValue'], cn['MaxValue'])
            if cn['MaxValue']>=1000:
                mult=1000
            else:
                mult=1
            cv2.createTrackbar(f'{key}', 'FalconControls',\
                 int(cn['MinValue']/mult), int(cn['MaxValue']/mult), partial(self.cb,key))
        FIRST=True
        f=0.90

        while True:  # show streamed images until Ctrl-C
            queue, image = self.image_hub.recv_any()
            self.msg=json.loads(queue)
            k=cv2.waitKey(1)
            logging.debug(f'times_interval:{self.msg["times_interval"]}')
            if self.msg['image_type']=='jpg':
                img=cv2.imdecode(image,1)
            else:
                img=image

            if k%256 == 32:
                msg=self.msg
                CCDsize=(int(msg['camera_info']['MaxWidth']),int(msg['camera_info']['MaxHeight']))
                imgSize=(img.shape[1],img.shape[0])
                fCCDsize=(CCDsize[0]/imgSize[0],CCDsize[0]/imgSize[0])
                rect=cv2.selectROI("FalconViewer",img, False)
                #newSize=(abs(rect[2]-rect[0]),abs(rect[3]-rect[1]))
                #newOrigin=(min(rect[2],rect[0]),min(rect[3],rect[1]))
                newSize=(rect[2],rect[3])
                newOrigin=(rect[0],rect[1])
                fnewSize=(int(fCCDsize[0]*newSize[0]),int(fCCDsize[1]*newSize[1]))
                fnewOrigin=(int(fCCDsize[0]*newOrigin[0]),int(fCCDsize[1]*newOrigin[1]))
                logging.info(f'CCDSize:{CCDsize} imgSize:{imgSize} fCCDsize:{fCCDsize}')
                logging.info(f'Selected:{rect} newSize:{newSize} newOrigin:{newOrigin}')
                logging.info(f'CCD:newSize:{fnewSize} newOrigin:{fnewOrigin}')
                self.setROI(fnewOrigin,fnewSize)
                
            if not FIRST and ((image.shape!=accumulated.shape) or (image.dtype!=accumulated.dtype)):
                FIRST=True

            if FIRST:
                #self.set_trackbars()
                accumulated=img
                FIRST=False
            else:
                accumulated=cv2.addWeighted(accumulated,f,img,1-f,0)
            screen=accumulated.copy()
            self.displayBoard(screen)
            cv2.imshow('FalconViewer', screen)           


if __name__ == '__main__':
    # construct the argument parser and parse command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--cameraServerIP", type=str, default='localhost',
        help="ip address of Camera Server")

    args = vars(ap.parse_args())
    logging.info(f"Connecting to:{args['cameraServerIP']}...")
    viewer=falconViewer(args['cameraServerIP'])
    logging.info(f"{args['cameraServerIP']} CONNETED")
    viewer.run()
