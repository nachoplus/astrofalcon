import cv2
import imageTransport
import datetime
import json
import argparse
import logging
import numpy as np
import astropy.io.fits as pyfits
from photutils import DAOStarFinder
from astropy.stats import sigma_clipped_stats

def takePicture():

    img=cv2.imread('output/20201024013736_ZWO_ASI294MC_Pro.tiff')
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean, median, std = sigma_clipped_stats(gray, sigma=3.0)
    print(f'mean:{mean} median:{median} std:{std}')
    daofind = DAOStarFinder(fwhm=5.0, threshold=5.*std)  
    print(gray.shape,median.shape)
    sources = daofind(gray - median)  
    for col in sources.colnames:  
        sources[col].info.format = '%.8g'  # for consistent table output
    print(sources)

    import numpy as np
    import matplotlib.pyplot as plt
    from astropy.visualization import SqrtStretch
    from astropy.visualization.mpl_normalize import ImageNormalize
    from photutils import CircularAperture
    positions = np.transpose((sources['xcentroid'], sources['ycentroid']))
    apertures = CircularAperture(positions, r=4.)
    norm = ImageNormalize(stretch=SqrtStretch())
    plt.imshow(gray, cmap='Greys', origin='lower', norm=norm,
            interpolation='nearest')
    apertures.plot(color='blue', lw=1.5, alpha=0.5)
    plt.savefig('kk.png')
    cv2.namedWindow('Falcon')
    cv2.imshow('Falcon', gray) 
    cv2.waitKey(0)
    
    return 

if __name__ == '__main__':
    takePicture()



