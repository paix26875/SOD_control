from cv2 import VideoCapture
import pyautogui
import sys
import time
from temp import setting
screen_x,screen_y = pyautogui.size()
curmus_x,curmus_y = pyautogui.position()

info = setting.info
x = info["capture_button_x"]
y = info["capture_button_y"]
vc = info["video_capture"]

print (u"現在のマウス位置 [" + str(curmus_x) + "]/[" + str(curmus_y) + "]")
pyautogui.moveTo(x, y, duration=0.1)
pyautogui.click(x, y)
if vc:
  time.sleep(2)
  pyautogui.click(x,y)