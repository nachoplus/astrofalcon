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
import baseClient
import datetime

logging.basicConfig(format='%(asctime)s %(levelname)s:falconCheckSpeed %(message)s',level=logging.INFO)


class falconViewer(baseClient.baseClient):
    def __init__(self,cameraServerIP):
        super().__init__(cameraServerIP)     
        logging.info("Starting falcon Camara Checkspeed")
  
    def run(self):
        while True:  # show streamed images until Ctrl-C
            queue, image = self.image_hub.recv_any()
            self.msg=json.loads(queue)
            k=cv2.waitKey(1)
            logging.debug(f'times_interval:{self.msg["times_interval"]}')
            if self.msg['image_type']=='jpg':
                img=cv2.imdecode(image,1)
            else:
                img=image
            now=datetime.datetime.now()
            times_end=datetime.datetime.strptime(self.msg["times_end"],'%Y-%m-%d %H:%M:%S.%f')
            logging.info(f'Network lag: {str(now-times_end)} EXP:{self.msg["times_interval"]} SIZE:{img.size}')


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
