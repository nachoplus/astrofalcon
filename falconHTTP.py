# run this program on the Mac to display image streams from multiple RPis
import cv2
import imageTransport
import falconHelper
from flask import Response
from flask import Flask
from flask import render_template
import threading
import argparse
import time
import logging
import json


# initialize a flask object
app = Flask(__name__)

logging.basicConfig(format='%(asctime)s %(levelname)s:falconHTTP %(message)s',level=logging.DEBUG)


def generate():
    import baseClient
    cameraServerIP=app.config.get('cameraServerIP')
    hub=baseClient.baseClient(cameraServerIP=cameraServerIP)
    imagesStack=[]
    while True:
        frame=hub.getFrame()
        frame,imagesStack=falconHelper.average(frame,imagesStack,n=5)
        frame=hub.displayBoard(frame)
        jpg=hub.raw2jpg(frame)
        yield(b'--frame\r\n' b'Content-Type: image/jpg\r\n\r\n' + 
                bytearray(jpg) + b'\r\n')

@app.route("/")
def index():
    # return the rendered template
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(),
        mimetype = "multipart/x-mixed-replace; boundary=frame")



# check to see if this is the main thread of execution
if __name__ == '__main__':
    # construct the argument parser and parse command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--ip", type=str, default='0.0.0.0',
        help="http ip address")
    ap.add_argument("-o", "--port", type=int, default=8088,
        help="http port number of the server (1024 to 65535)")
    ap.add_argument("-d", "--cameraServerIP", type=str, default='localhost',
        help="ip address of Camera Server")

    args = vars(ap.parse_args())
    logging.info(f"Connecting to:{args['cameraServerIP']}")
    logging.info(f"HHTP Server on:{args['cameraServerIP']}:{args['port']}")
    app.config['cameraServerIP'] =args['cameraServerIP']
    app.run(host=args["ip"], port=args["port"], debug=True,
        threaded=True, use_reloader=False)

