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

logging.basicConfig(format='%(asctime)s %(levelname)s:baseClient %(message)s',level=logging.INFO)


class baseClient:
    def __init__(self,cameraServerIP='localhost',controlSet={}):
        logging.info(f"Starting falcon Client.") 
        logging.info(f"Connecting to: tcp://{cameraServerIP}:5555")
        self.image_hub = imageTransport.ImageHub(open_port=f'tcp://{cameraServerIP}:5555', REQ_REP=False)
        _msg, _image = self.image_hub.recv_any()
        self.msg=json.loads(_msg)
        self.controls=self.msg['controls']
        self.zmqcontext = zmq.Context()
        self.CmdSocket = self.zmqcontext.socket(zmq.REQ)
        self.CmdSocket.connect(f'tcp://{cameraServerIP}:5556')
        
    def cb(self,key,x):
        if not key in self.controls.keys():
                logging.info(f"Invalid control. {key} do not exist")                
                return
        cn=self.controls[key]
        if x < cn['MinValue'] or x >cn['MaxValue']:
                logging.info(f"Invalid value for {key} control. {x} is not in {cn['MaxValue']}..{cn['MaxValue']} range")
                return
        ControlType=cn['ControlType']
        d=dict()
        d={'set_control_value':{ControlType:x}}   
        logging.info(f'Sending {d}')
        self.CmdSocket.send_string(json.dumps(d))
        reply = self.CmdSocket.recv()
        logging.info(reply)   
             
    def listControls(self):
        for key,cn in self.controls.items():
                if not cn['IsWritable']:
                        continue    
                print(f"{key} min:{cn['MinValue']} max:{cn['MaxValue']}")    
        return self.controls

    def setControls(self,controlsSet):
        for key,value in controlsSet.items():
                logging.info(f'Setting {key} = {value}')
                self.cb(key,value)
                        
    def getFrame(self,jpg=False):
        queue, image = self.image_hub.recv_any()
        self.arrivalTime=datetime.datetime.now()
        self.msg=json.loads(queue)
        logging.debug(f'times_interval:{self.msg["times_interval"]}')
        if not jpg:
                if self.msg['image_type']=='jpg':
                        img=cv2.imdecode(image,1)
                else:
                        img=image
        else:
                if self.msg['image_type']=='jpg':
                    img=image
                else:
                    (flag, img) = cv2.imencode(".jpg", image)
        return img
            
    def raw2jpg(self,image):
              (flag, img) = cv2.imencode(".jpg", image)
              return img
              
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
            times_end=datetime.datetime.strptime(self.msg["times_end"],'%Y-%m-%d %H:%M:%S.%f')
            now=datetime.datetime.now()

            self.textOverlay(4,img,now.strftime('Now: %Y-%m-%d %H:%M:%S.%f'))
            self.textOverlay(1,img,f'START:{self.msg["times_start"]}')
            self.textOverlay(2,img,f'END:{self.msg["times_end"]}')
            self.textOverlay(3,img,f'Exposure:{self.msg["times_interval"]}')
            self.textOverlay(5,img,f'Network lag: {str(self.arrivalTime-times_end)}')
            self.textOverlay(6,img,f'Processing time: {str(now-self.arrivalTime)}')
            self.textOverlay(7,img,f'Total lag: {str(now-times_end)}')
            print(f'msg: {self.msg["image_type"]}')
            return img


