#!/usr/bin/env python3

import argparse
import os
import sys
import time
import zwoasi as asi
import astropy.io.fits as pyfits


__author__ = 'Nacho Mas'
__version__ = '0.0.1'
__license__ = 'MIT'


class asi_camera:
        def __init__(self):
                env_filename = os.getenv('ZWO_ASI_LIB')
                asi.init(env_filename)
                num_cameras = asi.get_num_cameras()
                if num_cameras == 0:
                    print('No cameras found')
                    sys.exit(0)
                cameras_found = asi.list_cameras()  # Models names of the connected cameras 
                for n in range(num_cameras):
                    print('    %d: %s' % (n, cameras_found[n]))
                camera_id = 0
                print('Using #%d: %s' % (camera_id, cameras_found[camera_id]))

                self.camera = asi.Camera(camera_id)
                self.camera_name=cameras_found[0]
                self.camera_info = self.camera.get_camera_property()
                # Get all of the camera controls
                print('')
                print('Camera controls:')
                controls = self.camera.get_controls()
                for cn in sorted(controls.keys()):
                    print('    %s:' % cn)
                    for k in sorted(controls[cn].keys()):
                        print('        %s: %s' % (k, repr(controls[cn][k])))

                # Use minimum USB bandwidth permitted
                self.camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, self.camera.get_controls()['BandWidth']['MaxValue'])

        def info(self):
                pass


        def save_control_values(self,filename, settings):
                    filename += '.txt'
                    with open(filename, 'w') as f:
                        for k in sorted(settings.keys()):
                            f.write('%s: %s\n' % (k, str(settings[k])))
                    print('Camera settings saved to %s' % filename)

        def cooler(self,target_temp=-10):
                self.camera.set_control_value(asi.ASI_COOLER_ON, 1)
                self.camera.set_control_value(asi.ASI_FAN_ON, 1)
                self.camera.set_control_value(asi.ASI_TARGET_TEMP, target_temp)

        def get_temp(self):
                l=self.camera.get_control_value(asi.ASI_TEMPERATURE)[0]/10
                return l

        def setparms(self,exp,gain):
                # Set some sensible defaults. They will need adjusting depending upon
                # the sensitivity, lens and lighting conditions used.
                self.camera.disable_dark_subtract()
                self.camera.set_control_value(asi.ASI_GAIN, gain)
                self.camera.set_control_value(asi.ASI_EXPOSURE, exp*1000)
                self.camera.set_control_value(asi.ASI_WB_B, 50)
                self.camera.set_control_value(asi.ASI_WB_R, 50)
                self.camera.set_control_value(asi.ASI_GAMMA, 50)
                self.camera.set_control_value(asi.ASI_BRIGHTNESS, 20)
                self.camera.set_control_value(asi.ASI_FLIP, 0)

        def shoot(self,exp=1,gain=117,filename='image_mono16.fit'):
                self.setparms(exp,gain)
                print('Enabling stills mode')
                try:
                    # Force any single exposure to be halted
                    self.camera.stop_video_capture()
                    self.camera.stop_exposure()
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    pass

                print('Capturing a single 16-bit mono image')
                self.camera.set_image_type(asi.ASI_IMG_RAW16)
                imarray=self.camera.capture(filename=None)
                if filename is not None:
                        hdu = pyfits.PrimaryHDU(imarray)
                        hdu.header['CAMERA']=self.camera_name
                        hdu.header['GAIN']=gain
                        hdu.header['EXPOSURE']=float(exp/1000.)
                        hdu.header['CCD-TEMP']=float(self.get_temp())
                        hdu.header['OWNER']="NACHO MAS"
                        hdu.writeto(filename)
                else:
                        print("Filename not set")
                        
                print('Saved to %s' % filename)
                self.save_control_values(filename, self.camera.get_control_values())


if __name__ == '__main__':
    import time
    c=asi_camera()
    c.cooler()
    while c.get_temp()>-10:
        time.sleep(5)
        print(c.get_temp())
    c.shoot(exp=1,gain=120,filename='testRAW16.fit')
        
