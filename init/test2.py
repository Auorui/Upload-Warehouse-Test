import cv2
import numpy as np

def meanblur(img, ksize):
    """均值滤波 """
    blur_img = cv2.blur(img, ksize=ksize)
    return blur_img