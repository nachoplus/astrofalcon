#!/usr/bin/env python

import argparse
import os
import sys
import time
import datetime
import zwoasi as asi
import imagezmq
import argparse
import socket
import cv2
import json

__author__ = 'Nacho Mas'
__version__ = '0.1.0'
__license__ = 'MIT'


class ZWOcamera:
    def __init__(self):
        self.env_filename = os.getenv('ZWO_ASI_LIB')

        if self.env_filename:
            asi.init(self.env_filename)
        else:
            print('The filename of the SDK library is required \
                (or set ZWO_ASI_LIB environment variable with the filename)')
            sys.exit(1)

        num_cameras = asi.get_num_cameras()
        if num_cameras == 0:
            print('No cameras found')
            sys.exit(0)

        cameras_found = asi.list_cameras()  # Models names of the connected cameras

        if num_cameras == 1:
            camera_id = 0
            print('Found one camera: %s' % cameras_found[0])
        else:
            print('Found %d cameras' % num_cameras)
            for n in range(num_cameras):
                print('    %d: %s' % (n, cameras_found[n]))
            # TO DO: allow user to select a camera
            camera_id = 0
            print('Using #%d: %s' % (camera_id, cameras_found[camera_id]))

        self.camera = asi.Camera(camera_id)
        self.camera_info = self.camera.get_camera_property()
        self.controls = self.camera.get_controls()
        self.init()
        # Accept connections on all tcp addresses, port 5555
        self.sender = imagezmq.ImageSender(connect_to='tcp://*:5555' ,REQ_REP=False)

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

        while True:
            self.controls = self.camera.get_controls()
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
            values['controls']=self.controls

            resized=cv2.resize(img,dsize,cv2.INTER_NEAREST)
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            result, encimg = cv2.imencode('.jpg', resized, encode_param)
            self.sender.send_image(json.dumps(values), encimg)
            #self.sender.send_image('resizedRAW', resized)
            #self.sender.send_image('resizedJPG', encimg)


if __name__ == '__main__':

    camera=ZWOcamera()
    camera.run()
