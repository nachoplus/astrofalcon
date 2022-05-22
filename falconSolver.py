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
    
logging.basicConfig(format='%(asctime)s %(levelname)s:falconViewer %(message)s',level=logging.INFO)


def plate_solve(fname, L=3, H=7, ra=None, dec=None):
    dirn = 'astrometry_output'
    wcsfile = f"{dirn}/{fname.split('/')[-1]}.wcs"
    axyfile = f"{dirn}/{fname.split('/')[-1]}.axy"
    print(wcsfile)    
    print("Plate-solving...")
    params = ["solve-field", "--overwrite", "-z2", "-L", str(L), "-H", str(H),
        "-Nnone", "--match", "none", "--rdls", "none", "--corr", "none",
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
        os.remove(wcsfile)
    else:
        print("FAIL TO SOLVE")
        return (None,None),None
    os.remove(axyfile)
    #return SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs'), pixel_scale    
    return (ra, dec), pixel_scale    

class falconSolver(baseClient.baseClient):
    def __init__(self,cameraServerIP):
        logging.info("Starting falcon Solver")
        super().__init__(cameraServerIP)
        cv2.namedWindow('FalconSolver')



    def run(self):
     
        values=[]
        while True:  # show streamed images until Ctrl-C         
            k=cv2.waitKey(1)
            img=self.getFrame()     
            print(img.shape)    
            #Convert to PIL
            pilimg=Image.fromarray(img)
            tempfile = MemoryTempfile()
            # Write PIL Image to in-memory PNG
            ffile=tempfile.NamedTemporaryFile()
            fname=ffile.name
            print(fname)
            pilimg.save(fname, format="png")    
            (ra,dec),pixel=plate_solve(fname, L=3, H=70, ra=None, dec=None)
            values.append([ra,dec,pixel])
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
