# run this program on the Mac to display image streams from multiple RPis
import cv2
import imageTransport
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
    cameraServerIP=app.config.get('cameraServerIP')
    # grab global references to the output frame and lock variables
    # loop over frames from the output stream
    image_hub = imageTransport.ImageHub(open_port=f'tcp://{cameraServerIP}:5555', REQ_REP=False)
    while True:
        queue, image =image_hub.recv_any()
        print(queue)
        msg=json.loads(queue)
        
        if msg['image_type']=='jpg':
            #img=cv2.imdecode(image,1)
            encodedImage=image
        else:
            img=image
            (flag, encodedImage) = cv2.imencode(".jpg", img)
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
    ap.add_argument("-i", "--ip", type=str, default='0.0.0.0',
        help="ip address of the device")
    ap.add_argument("-o", "--port", type=int, default=8088,
        help="ephemeral port number of the server (1024 to 65535)")
    ap.add_argument("-d", "--cameraServerIP", type=str, default='localhost',
        help="ip address of Camera Server")

    args = vars(ap.parse_args())
    logging.info(f"Connecting to:{args['cameraServerIP']}")
    logging.info(f"HHTP Server on:{args['cameraServerIP']}:{args['port']}")
    app.config['cameraServerIP'] =args['cameraServerIP']
    app.run(host=args["ip"], port=args["port"], debug=True,
        threaded=True, use_reloader=False)

