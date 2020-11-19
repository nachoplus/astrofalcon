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
import datetime

logging.basicConfig(format='%(asctime)s %(levelname)s:falconBase %(message)s',level=logging.INFO)


class falconBase:
    def __init__(self,cameraServerIP='localhost'):
        logging.info("Starting falcon Camara Viewer")
        self.image_hub = imageTransport.ImageHub(open_port=f'tcp://{cameraServerIP}:5555', REQ_REP=False)
        _msg, _image = self.image_hub.recv_any()
        self.msg=json.loads(_msg)
        self.controls=self.msg['controls']
        print(self.controls)
        self.zmqcontext = zmq.Context()
        self.CmdSocket = self.zmqcontext.socket(zmq.REQ)
        self.CmdSocket.connect(f'tcp://{cameraServerIP}:5556')

        #self.update()

    def setROI(self,fnewOrigin,fnewSize):
        d=dict()
        d={'ROI':{'fnewOrigin':fnewOrigin,'fnewSize':fnewSize}}   
        logging.info(f'Sending {d}')
        self.CmdSocket.send_string(json.dumps(d))
        reply = self.CmdSocket.recv()
        logging.info(reply)        


    def textOverlay(self,line,img,text):
        font                   = cv2.FONT_HERSHEY_SIMPLEX
        bottomLeftCornerOfText = (20,20*line)
        fontScale              = 0.5
        fontColor              = (255,255,255)
        lineType               = 1

        cv2.putText(img,text, 
            bottomLeftCornerOfText, 
            font, 
            fontScale,
            fontColor,
            lineType)

    def displayBoard(self,img):
            self.textOverlay(1,img,f'START:{self.msg["times_start"]}')
            self.textOverlay(2,img,f'END:{self.msg["times_end"]}')
            self.textOverlay(3,img,f'ELAPSE:{self.msg["times_interval"]}')
            now=datetime.datetime.now()
            times_end=datetime.datetime.strptime(self.msg["times_end"],'%Y-%m-%d %H:%M:%S.%f')
            self.textOverlay(4,img,now.strftime('%Y-%m-%d %H:%M:%S.%f'))
            self.textOverlay(5,img,f'Network lag: {str(now-times_end)}')
            


