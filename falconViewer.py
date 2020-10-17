# run this program on the Mac to display image streams from multiple RPis
import cv2
import imagezmq
import zmq
import numpy as np
import json
from functools import partial
import argparse
import logging
import threading


logging.basicConfig(format='%(asctime)s %(levelname)s:falconViewer %(message)s',level=logging.DEBUG)


class falconViewer:
    def __init__(self,cameraServerIP):
        logging.info("Starting falcon Camara Viewer")
        self.image_hub = imagezmq.ImageHub(open_port=f'tcp://{cameraServerIP}:5555', REQ_REP=False)
        queue, image = self.image_hub.recv_image()
        msg=json.loads(queue)
        self.controls=msg['controls']
        self.zmqcontext = zmq.Context()
        self.CmdSocket = self.zmqcontext.socket(zmq.REQ)
        self.CmdSocket.connect(f'tcp://{cameraServerIP}:5556')
        self.msg=None
        #self.update()

    def update(self):
        if not self.msg is None:
            self.set_trackbars()
        threading.Timer(.10, self.update).start()



    def set_trackbars(self):
        self.control_values=self.msg['controls_values']
        values=self.control_values
        for key,cn in self.controls.items():
            if cv2.getTrackbarPos(f'{key}', 'FalconViewer')!=values[key]:
                cv2.setTrackbarPos(f'{key}', 'FalconViewer', values[key]) 

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
        d={ControlType:x*mult}   
        logging.info(f'Sending {d}')
        self.CmdSocket.send_string(json.dumps(d))
        reply = self.CmdSocket.recv()
        logging.info(reply)

    def run(self):
        cv2.namedWindow('FalconViewer')
        for key,cn in self.controls.items():
            if not cn['IsWritable']:
                continue
            print(key,  cn['MinValue'], cn['MaxValue'])
            if cn['MaxValue']>=1000:
                mult=1000
            else:
                mult=1
            cv2.createTrackbar(f'{key}', 'FalconViewer',\
                 int(cn['MinValue']/mult), int(cn['MaxValue']/mult), partial(self.cb,key))
        FIRST=True
        f=0.90
        while True:  # show streamed images until Ctrl-C
            queue, image = self.image_hub.recv_image()
            self.msg=json.loads(queue)
            logging.debug(f'times_interval:{self.msg["times_interval"]}')

            if self.msg['image_type']=='jpg':
                img=cv2.imdecode(image,1)
            else:
                img=image

            if FIRST:
                self.set_trackbars()
                accumulated=img
                FIRST=False
            else:
                accumulated=cv2.addWeighted(accumulated,f,img,1-f,0)
            cv2.imshow('FalconViewer', accumulated)           
            cv2.waitKey(1)

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
