img_name = 'orgimg_4.jpg'

import cv2
import numpy as np
import random

img = cv2.imread(img_name, 0)

cv2.imshow('gray', img)
key = cv2.waitKey(0) & 0xFF
cv2.destroyAllWindows()

dst = cv2.GaussianBlur(img, (0, 0), 7)

cv2.imshow('filter', dst)
key = cv2.waitKey(0) & 0xFF
cv2.destroyAllWindows()

ret, dst = cv2.threshold(dst, 45, 255, cv2.THRESH_BINARY)

cv2.imshow('contrast', dst)
key = cv2.waitKey(0) & 0xFF
cv2.destroyAllWindows()

cont, hier = cv2.findContours(dst, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_L1)

print(cont)

rgb_image = cv2.cvtColor(dst, cv2.COLOR_GRAY2RGB)

c = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
cv2.drawContours(rgb_image, cont, 0, c, 2, cv2.LINE_8, hier)

cv2.imshow('contour', rgb_image)
key = cv2.waitKey(0) & 0xFF
cv2.destroyAllWindows()