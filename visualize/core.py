"""
Copyright (c) 2023, Auorui.
All rights reserved.

This module is used for visualizing useful functions.
"""
import cv2
import time
import logging
import numpy as np
from functools import wraps

import pyzjr.Z as Z
from pyzjr.visualize.io import StackedImagesV1, VideoCap


class FPS:
    """
    Detect video frame rate and refresh the video display
    Examples:
    ```
        fpsReader = FPS()
        Vcap = VideoCap(mode=0)
        while True:
            img = Vcap.read()
            fps, img = fpsReader.update(img)
            Vcap.show("ss", img)
    ```
    """
    def __init__(self):
        self.pTime = time.time()

    def update(self, img=None, pos=(20, 50), color=(255, 0, 0), scale=3, thickness=3):
        """
        Update frame rate
        :param img: The displayed image can be left blank if only the fps value is needed
        :param pos: Position on FPS on image
        :param color: The color of the displayed FPS value
        :param scale: The proportion of displayed FPS values
        :param thickness: The thickness of the displayed FPS value
        """
        cTime = time.time()
        try:
            fps = 1 / (cTime - self.pTime)
            self.pTime = cTime
            if img is None:
                return fps
            else:
                cv2.putText(img, f'FPS: {int(fps)}', pos, cv2.FONT_HERSHEY_PLAIN,
                            scale, color, thickness)
                return fps, img
        except:
            return 0

class Timer:
    def __init__(self):
        """Start is called upon creation"""
        self.times = []
        self.start()
    def start(self):
        """initial time"""
        self.gap = time.time()
    def stop(self):
        """The time interval from the start of timing to calling the stop method"""
        self.times.append(time.time() - self.gap)
        return self.times[-1]
    def avg(self):
        """Average time consumption"""
        return sum(self.times) / len(self.times)
    def total(self):
        """Total time consumption"""
        return sum(self.times)
    def cumsum(self):
        """Accumulated sum of time from the previous n runs"""
        return np.array(self.times).cumsum().tolist()


class Runcodes:
    """
    Comparing the running time of different algorithms.
    Examples:
    ```
        with Runcodes("inference time"):
            output = ...
    ```
    """
    def __init__(self, description='Done'):
        self.description = description

    def __enter__(self):
        self.timer = Timer()
        return self

    def __exit__(self, *args):
        print(f'{self.description}: {self.timer.stop():.7f} sec')


def timing(decimal=5):
    """计时器装饰器，用于测量函数执行的时间。"""
    def decorator(function):
        @wraps(function)
        def timingwrap(*args, **kwargs):
            print(function.__name__, flush=True)
            start = time.perf_counter()
            res = function(*args, **kwargs)
            end = time.perf_counter()
            execution_time = end - start
            format_string = "{:.{}f}".format(execution_time, decimal)
            print(function.__name__, "delta time (s) =", format_string, flush=True)
            return res
        return timingwrap
    return decorator


class ColorFind():
    def __init__(self, trackBar=False, name="Bars"):
        self.trackBar = trackBar
        self.name = name
        if self.trackBar:
            self.initTrackbars()

    def empty(self, a):
        pass

    def initTrackbars(self):
        """
        :return:初始化轨迹栏
        """
        cv2.namedWindow(self.name)
        cv2.resizeWindow(self.name, 640, 240)
        cv2.createTrackbar("Hue Min", self.name, 0, 179, self.empty)
        cv2.createTrackbar("Hue Max", self.name, 179, 179, self.empty)
        cv2.createTrackbar("Sat Min", self.name, 0, 255, self.empty)
        cv2.createTrackbar("Sat Max", self.name, 255, 255, self.empty)
        cv2.createTrackbar("Val Min", self.name, 0, 255, self.empty)
        cv2.createTrackbar("Val Max", self.name, 255, 255, self.empty)

    def getTrackbarValues(self):
        """
        Gets the trackbar values in runtime
        :return: hsv values from the trackbar window
        """
        hmin = cv2.getTrackbarPos("Hue Min", self.name)
        smin = cv2.getTrackbarPos("Sat Min", self.name)
        vmin = cv2.getTrackbarPos("Val Min", self.name)
        hmax = cv2.getTrackbarPos("Hue Max", self.name)
        smax = cv2.getTrackbarPos("Sat Max", self.name)
        vmax = cv2.getTrackbarPos("Val Max", self.name)
        HsvVals = [[hmin, smin, vmin], [hmax, smax, vmax]]

        return HsvVals

    def protect_region(self, mask, threshold=None):
        """
        * 用于保护掩膜图的部分区域
        :param mask: 掩膜图
        :param threshold: 如果为None,则为不保护，如果是长为4的列表，则进行特定区域的保护
        :return: 返回进行保护区域的掩膜图

        example:    [0, img.shape[1], 0, img.shape[0]]为全保护状态，
                    x_start可以保护大于x的部分
                    x_end可以保护小于x的部分
                    y_start可以保护图像下方的部分
                    y_end可以保护图像上方的部分
        """
        if threshold == None:
            return mask
        else:
            x_start, x_end, y_start, y_end = threshold[:4]
            mask[y_start:y_end, x_start:x_end] = 0
            return mask

    def MaskZone(self, img, HsvVals):
        """
        * 生成掩膜图以及融合图像
        :param img: 输入图像
        :param HsvVals: 可以通过getTrackbarValues获得,也可调取Z.HSV的值
        :return: 返回融合图、掩膜图、HSV图
        """
        imgHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower = np.array(HsvVals[0])
        upper = np.array(HsvVals[1])
        mask = cv2.inRange(imgHSV, lower, upper)
        imgResult = cv2.bitwise_and(img, img, mask=mask)
        return imgResult, mask

    def update(self, img, myColor=None):
        """
        :param img: 需要在其中找到颜色的图像
        :param myColor: hsv上下限列表
        :return: mask带有检测到颜色的白色区域的roi图像
                 imgColor彩色图像仅显示检测到的区域
        """
        imgColor = [],
        mask = []
        if self.trackBar:
            myColor = self.getTrackbarValues()

        if isinstance(myColor, str):
            myColor = self.getColorHSV(myColor)

        if myColor is not None:
            imgColor, mask = self.MaskZone(img, myColor)
        return imgColor, mask

    def getColorHSV(self, myColor):
        if myColor == 'red':
            output = [[146, 141, 77], [179, 255, 255]]
        elif myColor == 'green':
            output = [[44, 79, 111], [79, 255, 255]]
        elif myColor == 'blue':
            output = [[103, 68, 130], [128, 255, 255]]
        else:
            output = None
            logging.warning("Color Not Defined")
            logging.warning("Available colors: red, green, blue ")

        return output

def DetectImageColor(img, ConsoleOut=True, threshold=None, scale=1.0):
    """
    * 轨迹栏检测图片,此函数仅仅作为使用示例
    :param img: 图片
    :param name: 轨迹栏名
    :param ConsoleOut: 用于是否控制台打印HsvVals的值
    :param threshold: 阈值，用于保护图片的区域
    :param scale: 规模大小
    :return:
    """
    ColF = ColorFind(True, "DetectImg")
    while True:
        imgHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        HsvVals = ColF.getTrackbarValues()
        if ConsoleOut:
            print(HsvVals)
        imgResult, mask = ColF.update(img,HsvVals)
        pro_mask = ColF.protect_region(mask, threshold)
        imgStack = StackedImagesV1(scale, ([img, imgHSV],[pro_mask,imgResult]))
        cv2.imshow("Stacked Images", imgStack)
        k = cv2.waitKey(1)
        if k == Z.Esc:
            break

def DetectVideoColor(mode=0, myColor=None, scale=1.0):
    """
    * 轨迹栏检测摄像头,此函数仅仅作为使用示例
    :param mode: 检测模式,默认本地摄像头,可传入video路径
    :param myColor: getColorHSV返回的一些测好的Hsv值
    :param scale: 规模大小
    """
    if myColor:
        Cf = False
    else:
        Cf = True
    Vcap = VideoCap(mode=mode)
    ColF = ColorFind(Cf, "DetectVideo")
    while True:
        img = Vcap.read()
        imgColor, mask = ColF.update(img, myColor)
        stackedimg = StackedImagesV1(scale, [img, imgColor])
        Vcap.show("DetectVideo", stackedimg)

if __name__=="__main__":
    # DetectVideo(myColor="red")
    @timing(decimal=5)
    def test_function():
        time.sleep(2.5)
    test_function()
    # imagePath = r"D:\PythonProject\pyzjr\pyzjr\test.png"
    # img = cv2.imread(imagePath)
    # DetectImageColor(img)