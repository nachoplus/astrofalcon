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
        self.camera_info = self.camera.get_camera_property()
        self.controls = self.camera.get_controls()
        self.controls_values =self.camera.get_control_values()
        self.init()
        # Accept connections on all tcp addresses, port 5555
        self.sender = imagezmq.ImageSender(connect_to='tcp://*:5555' ,REQ_REP=False)
        self.zmqcontext = zmq.Context()
        self.myCmdSocket = self.zmqcontext.socket(zmq.REP)        
        self.myCmdSocket.bind("tcp://*:5556")
        self.RUN = True
        self.CMDThread = self.zmqQueue()
        signal.signal(signal.SIGINT, self.signal_handler)


    def init(self):
        self.camera.set_control_value(asi.ASI_HIGH_SPEED_MODE, 1)
        self.camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, self.controls['BandWidth']['MaxValue'])

        # Set some sensible defaults. They will need adjusting depending upon
        # the sensitivity, lens and lighting conditions used.
        self.camera.disable_dark_subtract()
        self.camera.set_control_value(asi.ASI_GAIN, 560)
        self.camera.set_control_value(asi.ASI_EXPOSURE, 30000)
        self.camera.set_control_value(asi.ASI_WB_B, 50)
        self.camera.set_control_value(asi.ASI_WB_R, 50)
        self.camera.set_control_value(asi.ASI_GAMMA, 40)
        self.camera.set_control_value(asi.ASI_BRIGHTNESS,40)
        self.camera.set_control_value(asi.ASI_FLIP, 0)
        self.camera.set_image_type(asi.ASI_IMG_RGB24)
  

    def print_camera_controls(self):
        # Get all of the camera controls
        print('')
        print('Camera controls:')
        controls=self.controls
        for cn in sorted(controls.keys()):
            print('    %s:' % cn)
            for k in sorted(controls[cn].keys()):
                print('        %s: %s' % (k, repr(controls[cn][k])))
        return controls

    def run(self):
        #camera.set_roi_format(800*1,400*1,1,asi.ASI_IMG_RGB24)
        #camera.set_roi_start_position(0,0)
        self.camera.start_video_capture()
        img=self.camera.capture_video_frame()
        #percent by which the image is resized
        scale_percent = 20

        width = int(img.shape[1] * scale_percent / 100)
        height = int(img.shape[0] * scale_percent / 100)

        # dsize
        dsize = (width, height)
        #dsize = (1600, 1000)

        while self.RUN:
            start=datetime.datetime.now()
            img=self.camera.capture_video_frame()
            end=datetime.datetime.now()
            interval=end-start
            values={}
            values['times_start'] = start.strftime('%Y-%m-%d %H:%M:%S.%f')
            values['times_end'] = end.strftime('%Y-%m-%d %H:%M:%S.%f')
            values['times_interval'] = str(interval)
            values['image_type'] = 'jpg'
            values['camera_info']=self.camera_info
            values['controls']=self.camera.controls_values()

            resized=cv2.resize(img,dsize,cv2.INTER_NEAREST)
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            result, encimg = cv2.imencode('.jpg', resized, encode_param)
            self.sender.send_image(json.dumps(values), encimg)
            #self.sender.send_image('resizedRAW', resized)
            #self.sender.send_image('resizedJPG', encimg)
    
    def cmd(self,message):
        msg=json.loads(message)
        logging.info(msg)
        cn=int(list(msg.keys())[0])
        value=msg[list(msg.keys())[0]]
        self.camera.set_control_value(cn,value)
        return "OK"

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
