#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

import astropy.io.fits as pyfits
import numpy as np

class fitMaths():

	def __init__(self, fitsname):
		self.hdulist = pyfits.open(fitsname)
		header=self.hdulist[0].header
		(xsize,ysize)=(header['NAXIS1'],header['NAXIS2'])
		self.size=(xsize,ysize)
		self.fitsname=fitsname

	def __add__(self, other):
		new=fitMaths(self.fitsname)
		other=other.hdulist[0].data
		new.hdulist[0].data = new.hdulist[0].data + other
		return new

	def __sub__(self, other):
		new=fitMaths(self.fitsname)
		other=other.hdulist[0].data
		new.hdulist[0].data = new.hdulist[0].data - other
		return new

	def __div__(self, other):
		new=fitMaths(self.fitsname)
		other=other.hdulist[0].data
		new.hdulist[0].data = new.hdulist[0].data / other
		return new


	def __mul__(self, other):
		new=fitMaths(self.fitsname)
		other=other.hdulist[0].data
		new.hdulist[0].data = new.hdulist[0].data * other
		return new


	def __rmul__(self, scalar):
		new=fitMaths(self.fitsname)
		new.hdulist[0].data = scalar * new.hdulist[0].data 
		return new

	def rotate90(self,ccw=False):
		new=fitMaths(self.fitsname)
		(xsize,ysize)=self.size
		new.size=(ysize,xsize)
		new.hdulist[0].header['NAXIS1']=ysize
		new.hdulist[0].header['NAXIS2']=xsize
		#ccw ->Counter Clock Wise
		new.hdulist[0].data=np.transpose(new.hdulist[0].data)
		return new
	
			

	def dark(self, darkfitsname):
		dark = pyfits.open(darkfitsname)
		darkExp= float(dark[0].header['EXPTIME'])

		new=fitMaths(self.fitsname)
		newExp= float(new.hdulist[0].header['EXPTIME'])
		try:
			print ("TEMP FRAME:",new.hdulist[0].header['CCD-TEMP'],"TEMP DARK",dark[0].header['CCD-TEMP'])
		except:
			pass
		factor=newExp/darkExp
		print ('Appliying DARK newExp,darkExp,factor:',newExp,darkExp,factor)
		other=dark[0].data
		#print "Dark  shape:",other.shape
		#print "Light shape:",new.hdulist[0].data.shape
		new.hdulist[0].data = new.hdulist[0].data - factor * other
		return new

	def flat(self, flatfitsname):
		flat = pyfits.open(flatfitsname)
		flatExp= float(flat[0].header['EXPTIME'])

		new=fitMaths(self.fitsname)
		newExp= float(new.hdulist[0].header['EXPTIME'])
		other=flat[0].data
		print ('Appliying FLAT newExp,flatExp:',newExp,flatExp)
		new.hdulist[0].data = new.hdulist[0].data /  other 
		return new

	def save(self,filename):
		self.hdulist.writeto(filename,overwrite=True)


def SumFits(fits):
	return combine(fits,op='sum')

def combine(fits,combine='median'):
	op_dict={'median':np.median,'mean':np.mean,'max':np.max,'min':np.min,'sum':np.sum}
	for i,fit in enumerate(fits):
		if i==0:
			Master=fitMaths(fit)
			(xsize,ysize)=Master.hdulist[0].data.shape
			print("Combine:",combine)
			stackedData=Master.hdulist[0].data.reshape((-1))
			header=Master.hdulist[0].header
			print("FRAME:",i," mean/std:",stackedData.mean(),stackedData.std()) #,\
			#"EXP:",header['EXPTIME'],"ISO:",header['ISO'],"TEMP:",header['CCD-TEMP']
		else:
			frame=fitMaths(fit)
			frameData=frame.hdulist[0].data.reshape((-1))
			header=Master.hdulist[0].header
			print ("FRAME:",i," mean/std:",frameData.mean(),stackedData.std()) #,\
			#"EXP:",header['EXPTIME'],"ISO:",header['ISO'],"TEMP:",header['CCD-TEMP']
			stackedData=np.vstack((stackedData,frameData))
	if i==0:
		median=stackedData
		print ("Combining only 1 frame. Return as its")
	else:		
		median=op_dict[combine](stackedData,axis=0)
	print  ("combined fits mean/std",median.mean(),median.std())
	Master.hdulist[0].data=median.reshape((xsize,ysize))
	return Master


if __name__ == '__main__':
    '''
	Test
    '''
    f_light1=fitMaths('001558+114848-scan005-01.fit')
    f_dark=fitMaths('darkmedian2.fit')
    f_flat=fitMaths('flatmedian2.fit')
    r=(1/3)*f_light1
    r=f_light1/f_flat
    #dark_sustracted=f_light1.dark('darkmedian2.fit')
    #dark_sustracted.save('newimage.fits')
    flat_sustracted=f_light1.flat('flatmedian2.fit')
    flat_sustracted.save('newimage.fits')
