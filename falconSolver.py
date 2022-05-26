# run this program on the Mac to display image streams from multiple RPis
from sys import stderr
import cv2
import argparse
import logging
import baseClient
import os
import subprocess
from io import BytesIO
from PIL import Image
from memory_tempfile import MemoryTempfile
from astropy.io import fits
from astropy.wcs import WCS
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.time import Time, TimeDelta, TimezoneInfo
from astropy.wcs.utils import proj_plane_pixel_scales
import imageio
import datetime
import math

logging.basicConfig(format='%(asctime)s %(levelname)s:falconViewer %(message)s',level=logging.INFO)


def get_julian_datetime(date):
    """
    Convert a datetime object into julian float.
    Args:
        date: datetime-object of date in question

    Returns: float - Julian calculated datetime.
    Raises: 
        TypeError : Incorrect parameter type
        ValueError: Date out of range of equation
    """

    # Ensure correct format
    if not isinstance(date, datetime.datetime):
        raise TypeError('Invalid type for parameter "date" - expecting datetime')
    elif date.year < 1801 or date.year > 2099:
        raise ValueError('Datetime must be between year 1801 and 2099')

    # Perform the calculation
    julian_datetime = 367 * date.year - int((7 * (date.year + int((date.month + 9) / 12.0))) / 4.0) + int(
        (275 * date.month) / 9.0) + date.day + 1721013.5 + (
                          date.hour + date.minute / 60.0 + date.second / math.pow(60,
                                                                                  2)) / 24.0 - 0.5 * math.copysign(
        1, 100 * date.year + date.month - 190002.5) + 0.5

    return julian_datetime

def plate_solve(img, L=3, H=7, ra=None, dec=None):
    dirn = 'astrometry_output'
    #Convert to PIL
    pilimg=Image.fromarray(img)
    tempfile = MemoryTempfile()
    # Write PIL Image to in-memory PNG
    ffile=tempfile.NamedTemporaryFile()
    fname=ffile.name
    print(fname)
    pilimg.save(fname, format="png")    
    wcsfile = f"{dirn}/{fname.split('/')[-1]}.wcs"
    print(wcsfile)    
    print("Plate-solving...")
    params = ["solve-field", "--overwrite", "-z1", "-L", str(L), "-H", str(H),
        "-Nnone", "--match", "none", "--rdls", "none", "--corr", "none","--axy","none",
        "--solved", "none", "--index-xyls", "none", "-p", f"-D{dirn}","--cpulimit","30"]
    if ra is not None:
        params += ["--ra", str(ra)]
    if dec is not None:
        params += ["--dec", str(dec)]

    process=subprocess.Popen(params + [fname], stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    process.communicate()

    if os.path.exists(wcsfile):
        # Read world coordinate system
        hdu = fits.open(wcsfile)
        w = WCS(hdu[0].header)
        n, m, _ = imageio.imread(fname).shape

        # field center coordinates, offset=0
        radec = w.all_pix2world(m/2, n/2, 0)

        ra = float(radec[0])
        dec = float(radec[1])
        arcsec_per_pix = (proj_plane_pixel_scales(w)[0]*(u.degree/u.pixel)).to(u.arcsec/u.pixel)
        pixel_scale = arcsec_per_pix.value
        print(f"Detected center of image (Ra, Dec) = {ra}, {dec}")
        print(f"Pixel scale: {pixel_scale:.4} arcsec/px")
        #os.remove(wcsfile)
    else:
        print("FAIL TO SOLVE")
        return (None,None),None
    #return SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs'), pixel_scale    
    return (ra, dec), pixel_scale    

class falconSolver(baseClient.baseClient):
    def __init__(self,cameraServerIP):
        logging.info("Starting falcon Solver")
        super().__init__(cameraServerIP)
        cv2.namedWindow('FalconSolver')
        self.filelog="filelog.txt"

    def run(self):
        with open(self.filelog,"w") as fd:
            fd.write("JD;RA;DEC;PIXEL;START;INTERVAL;EXPOSURE\n")
        values=[]
        while True:  # show streamed images until Ctrl-C         
            k=cv2.waitKey(1)
            img=self.getFrame()    
            print(self.msg['times_start'])
            fmt='%Y-%m-%d %H:%M:%S.%f'
            times_start=datetime.datetime.strptime(self.msg['times_start'],fmt)
            times_end=datetime.datetime.strptime(self.msg['times_end'],fmt)
            exposure=datetime.timedelta(microseconds=int(self.msg["controls_values"]["Exposure"]))
            interval=times_end-times_start
            fecha=times_start+exposure/2
            print(img.shape)    
            (ra,dec),pixel=plate_solve(img,L=3, H=70, ra=None, dec=None)
            values=[str(x) for x in [get_julian_datetime(fecha),ra,dec,pixel,times_start,interval,exposure]]
            with open(self.filelog,"a") as fd:
                fd.write(";".join(values))
                fd.write('\n')

            print(values)

            cv2.imshow('FalconSolver', img)           


if __name__ == '__main__':
    # construct the argument parser and parse command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--cameraServerIP", type=str, default='localhost',
        help="ip address of Camera Server")
    args = vars(ap.parse_args())
    logging.info(f"Connecting to:{args['cameraServerIP']}...")
    solver=falconSolver(args['cameraServerIP'])
    logging.info(f"{args['cameraServerIP']} CONNETED")
    solver.run()
