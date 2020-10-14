# run this program on the Mac to display image streams from multiple RPis
import cv2
import imagezmq
import zmq
import numpy as np
import json
from functools import partial
import logging

class ValWithCallback(object):
    def __init__(self, val=0):
        self.val = val
    def change(self, val):
        self.val = val

class falconViewer:
    def __init__(self):
        logging.basicConfig(format='%(asctime)s %(levelname)s:falconViewer %(message)s',level=logging.DEBUG)
        logging.info("Starting falcon Camara Viewer")
        self.image_hub = imagezmq.ImageHub(open_port='tcp://localhost:5555', REQ_REP=False)
        queue, image = self.image_hub.recv_image()
        msg=json.loads(queue)
        self.controls=msg['controls']
        print(self.controls)
        self.zmqcontext = zmq.Context()
        self.CmdSocket = self.zmqcontext.socket(zmq.REQ)
        self.CmdSocket.connect("tcp://localhost:5556")

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
            cv2.createTrackbar(f'{key}{ mult if mult!=1 else ""}', 'FalconViewer',\
                 int(cn['MinValue']/mult), int(cn['MaxValue']/mult), partial(self.cb,key))


        while True:  # show streamed images until Ctrl-C
            queue, image = self.image_hub.recv_image()
            msg=json.loads(queue)
            logging.debug(f'times_interval:{msg["times_interval"]}')
            if msg['image_type']=='jpg':
                img=cv2.imdecode(image,1)
            else:
                img=image
            cv2.imshow('FalconViewer', img)
            cv2.waitKey(1)

if __name__ == '__main__':
    viewer=falconViewer()
    viewer.run()
