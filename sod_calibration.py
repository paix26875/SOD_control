from matplotlib import pyplot as plt
import numpy as np
from PIL import Image
import cv2
from icecream import ic
import os

if __name__ == '__main__':
  threshold = 223
  img_dir = os.path.dirname(os.getcwd() + os.sep + __file__) + os.sep + 'calibrationimg' + os.sep
  img = np.array(Image.open(img_dir + 'img_0011.bmp'))
  h,w,l = img.shape
  img_red = img[:,:,0]
  ret, img_thresh = cv2.threshold(img_red, threshold, 255, cv2.THRESH_BINARY)

  contours, _ = cv2.findContours(img_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

  maxCont=contours[0]
  for c in contours:
    if len(maxCont)<len(c):
      maxCont=c

  mu = cv2.moments(maxCont)
  # mu = cv2.moments(img_thresh, False)
  gravitypoint_x, gravitypoint_y= int(mu["m10"]/mu["m00"]) , int(mu["m01"]/mu["m00"])

  index = np.nonzero(img_thresh[:,gravitypoint_x])[0]
  ic(np.max(index)-np.min(index))
  # 重心を画像で表示
  cv2.circle(img_thresh, (gravitypoint_x, gravitypoint_y), 1, 100, 10, 20)
  plt.imshow(img_thresh)
  plt.colorbar()
  plt.show()
  ic(gravitypoint_x, gravitypoint_y)