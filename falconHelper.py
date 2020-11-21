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
import sep
import io
from PIL import Image
import matplotlib.pyplot as plt

logging.basicConfig(format='%(asctime)s %(levelname)s:falconHelper %(message)s',level=logging.DEBUG)



def average(img,imagesStack,n=20):
        # Generate noisy images using cv2.randn. Can use your own mean and std.
        imagesStack.append(img)
        nimages=len(imagesStack)
        if nimages>n:
                nimages=n
                imagesStack.pop(0)
        # For averaging create an empty array, then add images to this array.
        img_avg=np.zeros((img.shape[0],img.shape[1],img.shape[2]),np.float32)
        for im in imagesStack:
            img_avg=img_avg+im/nimages
            #img_avg=img_avg+im
        # Round the float values. Always specify the dtype
        img_avg=np.array(np.round(img_avg),dtype=np.uint8)
        return img_avg


def sources(image,thresholdSigma=1.5):
        if len(image.shape)>2:
           img=cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype('<f8')
        else:
           img=image.astype('<f8')
        bkg = sep.Background(img)
        thresh =  thresholdSigma * bkg.globalrms
        data_sub = img - bkg
        objects = sep.extract(data_sub, thresh)
        logging.info(f'GLOBAL RMS:{bkg.globalrms} num sources:{len(objects)}')
        return objects,bkg,data_sub

       
def drawSources(objects,img):
        color=(255,0,0)
        w=2
        idx=objects['flux'].argmax()
        for i,o in enumerate(objects):
                x0=int(objects['x'][i])
                y0=int(objects['y'][i])
                cv2.circle(img,(x0,y0),w,color,1)
        color=(0,0,255)
        x0=int(objects['x'][idx])
        y0=int(objects['y'][idx])
        cv2.rectangle(img,(x0-w,y0-w),(x0+w,y0+w),color,1)
        

def overlayGraph(img,values,title='FWHM'):
        plt.figure()
        plt.plot(values)
        plt.title(title)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        im = Image.open(buf)
        img1 = cv2.imread(buf, -1)
        buf.close()
        # apply the overlay
        cv2.addWeighted(img, alpha, img1, 1 - alpha,0, img)
        return img
	
def fwhm(objects):
        return 2 * np.sqrt(np.log(2)*(objects['x2'] + objects['y2']))

def background(video_frames):
        # type: (np.ndarray) -> np.ndarray
        """
        Create the background of a video via MOGs.

        :param video_frames: list of ordered frames (i.e., a video).
        :return: the estimated background of the video.
        """
        mog = cv2.createBackgroundSubtractorMOG2()
        for frame in video_frames:
            img = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            mog.apply(img)

        # Get background
        background = mog.getBackgroundImage()

        return cv2.cvtColor(background, cv2.COLOR_BGR2RGB)

'''
def motion(img,oldimg):
        # resize the frame, convert it to grayscale, and blur it
        frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        # if the first frame is None, initialize it
        if firstFrame is None:
                firstFrame = gray
        # compute the absolute difference between the current frame and
        # first frame
        frameDelta = cv2.absdiff(firstFrame, gray)
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
        # dilate the thresholded image to fill in holes, then find contours
        # on thresholded image
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        # loop over the contours
        for c in cnts:
                # if the contour is too small, ignore it
                if cv2.contourArea(c) < args["min_area"]:
                        continue
                # compute the bounding box for the contour, draw it on the frame,
                # and update the text
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                text = "Occupied"
        # draw the text and timestamp on the frame
        cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        # show the frame and record if the user presses a key
        cv2.imshow("Security Feed", frame)
        cv2.imshow("Thresh", thresh)
        cv2.imshow("Frame Delta", frameDelta)
        key = cv2.waitKey(1) & 0xFF
        # if the `q` key is pressed, break from the lop
        if key == ord("q"):
                break
'''       


