#!/usr/bin/env python

import argparse
import os
import sys
import time
import datetime
import zwoasi as asi
import zmq
import imagezmq
import argparse
import socket
import cv2
import json
import signal
import logging
import threading

lock = threading.Lock()

def threaded(fn):
    def wrapper(*args, **kwargs):
        t1 = threading.Thread(target=fn, args=args, kwargs=kwargs)
        t1.start()
        return t1

    return wrapper

__author__ = 'Nacho Mas'
__version__ = '0.1.0'
__license__ = 'MIT'


class ZWOcamera:
    TFORMAT_RAW=0
    TFORMAT_JPG=1

    def __init__(self):
        logging.basicConfig(format='%(asctime)s %(levelname)s:falcon ZWOcamera %(message)s',level=logging.INFO)
        logging.info("Starting falcon ZWO Camera Server")

        self.env_filename = os.getenv('ZWO_ASI_LIB')

        if self.env_filename:
            asi.init(self.env_filename)
        else:
            logging.error('The filename of the SDK library is required \
                (or set ZWO_ASI_LIB environment variable with the filename)')
            sys.exit(1)

        num_cameras = asi.get_num_cameras()
        if num_cameras == 0:
            logging.error('No cameras found')
            sys.exit(0)

        cameras_found = asi.list_cameras()  # Models names of the connected cameras

        if num_cameras == 1:
            camera_id = 0
            logging.info('Found one camera: %s' % cameras_found[0])
        else:
            logging.info('Found %d cameras' % num_cameras)
            for n in range(num_cameras):
                logging.info('    %d: %s' % (n, cameras_found[n]))
            # TO DO: allow user to select a camera
            camera_id = 0
            logging.info('Using #%d: %s' % (camera_id, cameras_found[camera_id]))

        self.camera = asi.Camera(camera_id)
        self.initCamera()
        # Accept connections on all tcp addresses, port 5555
        self.sender = imagezmq.ImageSender(connect_to='tcp://*:5555' ,REQ_REP=False)
        self.zmqcontext = zmq.Context()
        self.myCmdSocket = self.zmqcontext.socket(zmq.REP)        
        self.myCmdSocket.bind("tcp://*:5556")
        self.RUN = True
        self.CMDThread = self.zmqQueue()
        signal.signal(signal.SIGINT, self.signal_handler)


    def initCamera(self):
        self.camera_info = self.camera.get_camera_property()
        self.controls = self.camera.get_controls()
        self.numNativeControls=len(self.controls)
        self.addSoftControls()
        self.controls_values =self.camera.get_control_values()

        self.camera.set_control_value(asi.ASI_HIGH_SPEED_MODE, 1)
        self.camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, self.controls['BandWidth']['MaxValue'])

        self.camera.disable_dark_subtract()
        self.camera.set_control_value(asi.ASI_GAIN, 570)
        self.camera.set_control_value(asi.ASI_EXPOSURE, 500000)
        self.camera.set_control_value(asi.ASI_WB_B, 50)
        self.camera.set_control_value(asi.ASI_WB_R, 50)
        self.camera.set_control_value(asi.ASI_GAMMA, 30)
        self.camera.set_control_value(asi.ASI_BRIGHTNESS,40)
        self.camera.set_control_value(asi.ASI_FLIP, 0)
        self.Tformat=self.TFORMAT_JPG
        self.scale=20
        self.HWformat=asi.ASI_IMG_RGB24
        self.camera.set_image_type(self.HWformat)
        self.bins=1
  
    def addSoftControls(self):
        softControls={'Scale': {
                                    'Name': 'Scale',
                                    'Description': 'Transport scale',
                                    'MaxValue': 100,
                                    'MinValue': 10,
                                    'DefaultValue': 20,
                                    'IsAutoSupported': True,
                                    'IsWritable': True,
                                    'ControlType': 20},
                       'Tformat': {
                                    'Name': 'Tformat',
                                    'Description': 'Transport format',
                                    'MaxValue': 1,
                                    'MinValue': 0,
                                    'DefaultValue': 1,
                                    'IsAutoSupported': True,
                                    'IsWritable': True,
                                    'ControlType': 21},
                       'HWformat': {
                                    'Name': 'HWformat',
                                    'Description': 'Hardware format',
                                    'MaxValue': 2,
                                    'MinValue': 0,
                                    'DefaultValue':asi.ASI_IMG_RGB24,
                                    'IsAutoSupported': True,
                                    'IsWritable': True,
                                    'ControlType': 22},
                       'binning': {
                                    'Name': 'binning',
                                    'Description': 'Binning',
                                    'MaxValue': 3,
                                    'MinValue': 1,
                                    'DefaultValue': 0,
                                    'IsAutoSupported': True,
                                    'IsWritable': True,
                                    'ControlType': 23},

                    }
        self.controls.update(softControls)



    def run(self):
        self.camera.start_video_capture()

        while self.RUN:
            start=datetime.datetime.now()
            with lock:
                img=self.camera.capture_video_frame()
            #percent by which the image is resized
            scale_percent = self.scale
            width = int(img.shape[1] * scale_percent / 100)
            height = int(img.shape[0] * scale_percent / 100)
            dsize = (width, height)

            end=datetime.datetime.now()
            interval=end-start
            values={}
            values['times_start'] = start.strftime('%Y-%m-%d %H:%M:%S.%f')
            values['times_end'] = end.strftime('%Y-%m-%d %H:%M:%S.%f')
            values['times_interval'] = str(interval)

            values['camera_info']=self.camera_info
            values['controls']=self.controls
            values['controls_values']=self.camera.get_control_values()
            values['controls_values']['Scale']=self.scale
            values['controls_values']['Tformat']=self.Tformat
            values['controls_values']['HWformat']=self.HWformat
            values['controls_values']['binning']=self.bins
            resized=cv2.resize(img,dsize,cv2.INTER_NEAREST)

            if self.Tformat==self.TFORMAT_JPG:
                values['image_type'] = 'jpg'
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
                result, image = cv2.imencode('.jpg', resized, encode_param)
            else:
                values['image_type'] = 'raw'
                image=resized

            self.sender.send_image(json.dumps(values), image)

    def setROI(self,fnewOrigin,fnewSize):
        with lock:
            oldOrigin=self.camera.get_roi_start_position()
            logging.info(f'{oldOrigin}')
            self.camera.stop_video_capture()
            self.camera.set_roi( start_x=oldOrigin[0]+fnewOrigin[0], start_y=oldOrigin[1]+fnewOrigin[1],
                            width=8*int(fnewSize[0]/8),height=8*int(fnewSize[1]/8), bins=self.bins, image_type=self.HWformat)
            self.camera.start_video_capture()
    
    def cmd(self,message):
        msg=json.loads(message)
        logging.info(msg)
    
        if 'set_control_value' in msg:
            value=msg['set_control_value']
            for key,v in value.items():
                logging.info(f'{key}:{int(v)}')
                if int(key) <self.numNativeControls:
                    self.camera.set_control_value(int(key),int(v))
                else:  
                    if int(key)==20:        
                        self.scale=int(v)
                    if int(key)==21:
                        if int(v)==0:
                            self.Tformat=self.TFORMAT_RAW
                        else:
                            self.Tformat=self.TFORMAT_JPG
                    if int(key)==22:
                        if int(v)==0:
                            self.HWformat=asi.ASI_IMG_RAW8
                        if int(v)==1:
                            self.HWformat=asi.ASI_IMG_RAW16
                        if int(v)==2:
                            self.HWformat=asi.ASI_IMG_RGB24
                        with lock:
                            logging.debug("Changing img format")
                            self.camera.stop_video_capture()
                            self.camera.set_image_type(self.HWformat)
                            self.camera.start_video_capture()
                            logging.debug("Changed")
                    if int(key)==23:
                            pass


        if 'ROI' in msg:
            value=msg['ROI']
            fnewOrigin=value['fnewOrigin']
            fnewSize=value['fnewSize']
            self.setROI(fnewOrigin,fnewSize)


        return 'OK'

    @threaded
    def zmqQueue(self):
        '''this thread listen and process all the CMD from other nodes. **Run in background** '''
        while self.RUN:
            if True:
                try:
                        message = self.myCmdSocket.recv()
                        logging.debug("RECV CMD: %s", message)
                except:
                        self.myCmdSocket.close()
                        break

                #  Do some 'work'
                reply = self.cmd(message)
                logging.debug("SEND CMD response: %s", reply)
                #  Send reply back
                self.myCmdSocket.send_string(str(reply))
        logging.info("CMD LOOP END.")
        return

    def signal_handler(self, signal, frame):
        '''Capture Ctril+C key'''
        logging.info('You pressed Ctrl+C!')
        self.end()
        exit()

    def __del__(self):
        self.end()

    def end(self):    
        self.RUN = False
        self.myCmdSocket.close()
        logging.info("Term zmqcontext")
        self.zmqcontext.term()
        
        logging.info("Waiting CMDthread end")
        try:
                self.CMDThread.join()
        except:
                logging.warn("Can't join CMD thread")

        logging.info("***ENDED***")
        return

if __name__ == '__main__':

    camera=ZWOcamera()
    camera.run()
