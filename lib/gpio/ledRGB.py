#!/usr/bin/env python
#for RGB VCC/GND
# -*- coding: utf-8 -*-
import sys,os,time
import yaml

import RPi.GPIO

import lib.appPath
from lib.baseClass import AbstractClass


class LedRGB(AbstractClass):
    @classmethod
    def is_available(cls):
        return (super(cls, cls).is_available() and
                lib.diagnose.check_python_import('RPi.GPIO'))

    @classmethod
    def get_config(cls):
        config = {}
        config_path = os.path.join(lib.appPath.CONFIG_PATH, 'gpio.yml');
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                profile = yaml.safe_load(f)
                if 'ledRGB' in profile:
                    profile = profile['ledRGB']
                    if 'green_bcm' in profile:
                        config['green_bcm'] = profile['green_bcm']
                    if 'red_bcm' in profile:
                        config['red_bcm'] = profile['red_bcm']
                    if 'blue_bcm' in profile:
                        config['blue_bcm'] = profile['blue_bcm']
        return config

    def __init__(self,green_bcm,red_bcm,blue_bcm):

        RPi.GPIO.setmode(RPi.GPIO.BCM)

        RPi.GPIO.setup(red_bcm, RPi.GPIO.OUT)
        RPi.GPIO.setup(green_bcm, RPi.GPIO.OUT)
        RPi.GPIO.setup(blue_bcm, RPi.GPIO.OUT)
        
        self._pwmR = RPi.GPIO.PWM(red_bcm, 70)
        self._pwmG = RPi.GPIO.PWM(green_bcm, 70)
        self._pwmB = RPi.GPIO.PWM(blue_bcm, 70)

        self._pwmR.start(0)
        self._pwmG.start(0)
        self._pwmB.start(0)

    def bling(self):
        try:
            t = 0.4
            while True:
                # 红色灯全亮，蓝灯，绿灯全暗（红色）
                self._pwmR.ChangeDutyCycle(0)
                self._pwmG.ChangeDutyCycle(100)
                self._pwmB.ChangeDutyCycle(100)
                time.sleep(t)
                # 绿色灯全亮，红灯，蓝灯全暗（绿色）
                self._pwmR.ChangeDutyCycle(100)
                self._pwmG.ChangeDutyCycle(0)
                self._pwmB.ChangeDutyCycle(100)
                time.sleep(t)
                
                # 蓝色灯全亮，红灯，绿灯全暗（蓝色）
                self._pwmR.ChangeDutyCycle(100)
                self._pwmG.ChangeDutyCycle(100)
                self._pwmB.ChangeDutyCycle(0)
                time.sleep(t)
                
                # 红灯，绿灯全亮，蓝灯全暗（黄色）
                self._pwmR.ChangeDutyCycle(0)
                self._pwmG.ChangeDutyCycle(0)
                self._pwmB.ChangeDutyCycle(100)
                time.sleep(t)
                
                # 红灯，蓝灯全亮，绿灯全暗（洋红色）
                self._pwmR.ChangeDutyCycle(0)
                self._pwmG.ChangeDutyCycle(100)
                self._pwmB.ChangeDutyCycle(0)
                time.sleep(t)
                
                # 绿灯，蓝灯全亮，红灯全暗（青色）
                self._pwmR.ChangeDutyCycle(100)
                self._pwmG.ChangeDutyCycle(0)
                self._pwmB.ChangeDutyCycle(0)
                time.sleep(t)
                
                # 红灯，绿灯，蓝灯全亮（白色）
                self._pwmR.ChangeDutyCycle(0)
                self._pwmG.ChangeDutyCycle(0)
                self._pwmB.ChangeDutyCycle(0)
                time.sleep(t)

                # 调整红绿蓝LED的各个颜色的亮度组合出各种颜色
                for r in xrange (0, 101, 20):
                    self._pwmR.ChangeDutyCycle(r)
                    for g in xrange (0, 101, 20):
                        self._pwmG.ChangeDutyCycle(g)
                        for b in xrange (0, 101, 20):
                            self._pwmB.ChangeDutyCycle(b)
                            time.sleep(0.01)
                
        except KeyboardInterrupt:
            pass

        self.clear()

    def clear(self):
        self._pwmR.stop()
        self._pwmG.stop()
        self._pwmB.stop()
        
        RPi.GPIO.cleanup()
