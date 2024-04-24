import cv2
import time
import numpy as np
import Handtrackingmodule as htm
import math

from dataclasses import dataclass
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from src.exception import CustomException
from src.logger import logging

#Create a data class for cam variables
@dataclass
class Cam:
    '''
        Is a Special class, which automatically creates the special methods like __init__ and __repr__ 
        Will use it to store variables
        1. wCam -> width of the cam window
        2. hCam -> height of the cam window
        3.cap -> object for the cam window
        4. pTime -> previous time (used to calculate the frame rates)
        

    '''
    wCam =  640
    hCam =  480
    cap = cv2.VideoCapture(0)
    cap.set(3, wCam)
    cap.set(4,hCam)
    pTime = 0


#Create a data class for detector variable  
@dataclass
class Detector:
    '''
        Variable : detector -> object of hand detector class of Handtrackingmodule
    
    '''
    detector = htm.handDetector(detectionCon=0.7)


#Create a data class for Audio variables
@dataclass
class Audio:
    '''
        Variables:
            1. devices -> stores the speaker of the system
            2. interface -> interface to create a variable for volume 
            3. volume -> object that stores the actual volume of the system
            3. volRange -> range of the system volume
            4. minVol -> min volume of the system
            5. maxVol -> max volume of the system
            6. vol -> instance of system volume
            7. volBar -> creates a bar of volume
            8. volPer -> percentage of volume
            
    '''
 
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))

    volRange = volume.GetVolumeRange()
    minVol = volRange[0]
    maxVol = volRange[1]
    vol = 0
    volBar = 400
    volPer = 0

#Create a class to control the volume
class VolumeControl:
    def __init__(self) :
        '''
            Initialize the variables of the above data classes
        '''
        logging.info("Initializing the cam variables")
        self.Cam_variables = Cam()

        logging.info("Initializing the detector variables")
        self.Detector_variable = Detector()

        logging.info("Initializing the Audio variables")
        self.Audio_variables = Audio()

    #create a method to control the volume
    def control_volume(self):
        '''
            Function to handle the volume controls 
        '''
        while True:
            success, img = self.Cam_variables.cap.read()
            img = self.Detector_variable.detector.findHands(img)
            lmList = self.Detector_variable.detector.findPosition(img, draw=False)
            if len(lmList) != 0:
                
                # Defining the variable for the landmarks through which we will be controlling the volume
                x1, y1 = lmList[4][1], lmList[4][2]
                x2, y2 = lmList[8][1], lmList[8][2]
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        
                # Drawing a line between the above variables
                cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
                cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
                cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

                #Calulating the leghth of above created line 
                length = math.hypot(x2 - x1, y2 - y1)
        
                self.Audio_variables.vol = np.interp(length, [50, 300], [self.Audio_variables.minVol, self.Audio_variables.maxVol])
                self.Audio_variables.volBar = np.interp(length, [50, 300], [400, 150])
                self.Audio_variables.volPer = np.interp(length, [50, 300], [0, 100])
                self.Audio_variables.volume.SetMasterVolumeLevel(self.Audio_variables.vol, None)
            
                
                if length < 50:
                    cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)
        
            cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
            cv2.rectangle(img, (50, int(self.Audio_variables.volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
            cv2.putText(img, f'{int(self.Audio_variables.volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,1, (255, 0, 0), 3)
        
        
            cTime = time.time()
            fps = 1 / (cTime - self.Cam_variables.pTime)
            pTime = cTime
            cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX,1, (255, 0, 0), 3)
        
            cv2.imshow("Img", img)
            cv2.waitKey(1)
        
            if cv2.getWindowProperty("Img", cv2.WND_PROP_VISIBLE) <1:
                break

        
if __name__ == '__main__':
    Controller = VolumeControl()
    Controller.control_volume()