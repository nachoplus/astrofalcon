#!/usr/bin/env python3


base_dir='./kkcalibrationWB'
Ttarget=-20
darks_times=[1000,5000,10000,15000]                    #in ms
num_darks=10
gains=[1,100,200,300,400,500,570]
#gains=range(1,570,40)
num_bias=10
ETA=0
for g in gains:
	ETA+=num_bias
	for d in darks_times:
		ETA+=1+num_darks*d/1000


def CAPTURE_run():
	import zwoasi_cam
	import zwoasi as asi
	import os
	import time
	c=zwoasi_cam.asi_camera()
	c.cooler(target_temp=Ttarget)
	time.sleep(1)
	while True and abs(c.get_temp()-Ttarget)>=0.5:
                print("COOLER WAIT. TEMP:",c.get_temp()," CURRENT:",str(c.camera.get_control_value(asi.ASI_COOLER_POWER_PERC)[0]))
                time.sleep(1)

	print ("TEMP OK. STARTING...")
	for gain in gains:
                name=base_dir+'/GAIN'+str(gain)
                if not os.path.exists(name):
                    os.makedirs(name)
                bias_dir=name+'/BIAS'
                if not os.path.exists(bias_dir):
                    os.makedirs(bias_dir)
                darks_dir=name+'/DARKS'
                if not os.path.exists(darks_dir):
                    os.makedirs(darks_dir)
                for n in range(num_bias):
                        c.shoot(exp=1,gain=gain,filename=bias_dir+'/BIAS-'+str(n)+'.fit')
                for darktime in darks_times:
                        _darksdir=darks_dir+'/'+str(darktime)
                        if not os.path.exists(_darksdir):
                            os.makedirs(_darksdir)
                        for n in range(num_darks):
                                c.shoot(exp=darktime,gain=gain,filename=_darksdir+'/DARK-'+str(n)+'.fit')


if __name__ == '__main__':
	CAPTURE_run()




