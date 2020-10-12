#!/usr/bin/env python

import argparse
import os
import sys
import time
import zwoasi as asi
import imagezmq
import socket
import cv2

__author__ = 'Nacho Mas'
__version__ = '0.1.0'
__license__ = 'MIT'


def save_control_values(filename, settings):
    filename += '.txt'
    with open(filename, 'w') as f:
        for k in sorted(settings.keys()):
            f.write('%s: %s\n' % (k, str(settings[k])))
    print('Camera settings saved to %s' % filename)


env_filename = os.getenv('ZWO_ASI_LIB')

parser = argparse.ArgumentParser(description='Process and save images from a camera')
parser.add_argument('filename',
                    nargs='?',
                    help='SDK library filename')
args = parser.parse_args()

# Initialize zwoasi with the name of the SDK library
if args.filename:
    asi.init(args.filename)
elif env_filename:
    asi.init(env_filename)
else:
    print('The filename of the SDK library is required (or set ZWO_ASI_LIB environment variable with the filename)')
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

camera = asi.Camera(camera_id)
camera_info = camera.get_camera_property()

# Get all of the camera controls
print('')
print('Camera controls:')
controls = camera.get_controls()
for cn in sorted(controls.keys()):
    print('    %s:' % cn)
    for k in sorted(controls[cn].keys()):
        print('        %s: %s' % (k, repr(controls[cn][k])))


# Use minimum USB bandwidth permitted
camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, camera.get_controls()['BandWidth']['MinValue'])

# Set some sensible defaults. They will need adjusting depending upon
# the sensitivity, lens and lighting conditions used.
camera.disable_dark_subtract()

camera.set_control_value(asi.ASI_GAIN, 100)
camera.set_control_value(asi.ASI_EXPOSURE, 10000)
camera.set_control_value(asi.ASI_WB_B, 50)
camera.set_control_value(asi.ASI_WB_R, 50)
camera.set_control_value(asi.ASI_GAMMA, 50)
camera.set_control_value(asi.ASI_BRIGHTNESS,50)

# Accept connections on all tcp addresses, port 5555
sender = imagezmq.ImageSender(connect_to='tcp://*:5555' ,REQ_REP=False) 
camera.set_control_value(asi.ASI_FLIP, 0)

camera.set_image_type(asi.ASI_IMG_RGB24)
camera.set_roi_start_position(0,0)
#camera.set_roi_format(1500,500,1,asi.ASI_IMG_RGB24)
camera.start_video_capture()
img=camera.capture_video_frame()
#percent by which the image is resized
scale_percent = 20

#calculate the 50 percent of original dimensions
width = int(img.shape[1] * scale_percent / 100)
height = int(img.shape[0] * scale_percent / 100)

# dsize
dsize = (width, height)

while True:
    img=camera.capture_video_frame()

    resized=cv2.resize(img,dsize,cv2.INTER_NEAREST)
    #encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
    #result, encimg = cv2.imencode('.jpg', resized, encode_param)
    sender.send_image('resized', resized)
    #sender.send_image('resizedRAW', resized)
    #sender.send_image('resizedJPG', encimg)
    time.sleep(0.0001)
