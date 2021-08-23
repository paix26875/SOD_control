import pyautogui
import sys
import time
screen_x,screen_y = pyautogui.size()
curmus_x,curmus_y = pyautogui.position()

print (u"現在のマウス位置 [" + str(curmus_x) + "]/[" + str(curmus_y) + "]")
# pyautogui.moveTo(1017, 494, duration=0.1)
pyautogui.click(925, 488)