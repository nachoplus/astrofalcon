# run this program on the Mac to display image streams from multiple RPis
import cv2
import imagezmq
from flask import Response
from flask import Flask
from flask import render_template
import threading
import argparse
import time



# initialize a flask object
app = Flask(__name__)

def generate():
    # grab global references to the output frame and lock variables
    # loop over frames from the output stream
    image_hub = imagezmq.ImageHub(open_port='tcp://localhost:5555', REQ_REP=False)
    image_hub.connect('tcp://localhost:5555')
    while True:
        queue, outputFrame =image_hub.recv_image()
        (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
        # ensure the frame was successfully encoded
        # yield the output frame in the byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpg\r\n\r\n' + 
                bytearray(encodedImage) + b'\r\n')

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
    ap.add_argument("-i", "--ip", type=str, required=True,default='0.0.0.0',
        help="ip address of the device")
    ap.add_argument("-o", "--port", type=int, required=True,default=8088,
        help="ephemeral port number of the server (1024 to 65535)")
    args = vars(ap.parse_args())


    app.run(host=args["ip"], port=args["port"], debug=True,
        threaded=True, use_reloader=False)

