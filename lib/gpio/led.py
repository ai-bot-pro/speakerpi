#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys,os,time
import yaml
import RPi.GPIO as GPIO

import lib.appPath
from lib.baseClass import AbstractClass

class Led(AbstractClass):
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
                if 'led' in profile:
                    profile = profile['led']
                    if 'green_bcm' in profile:
                        config['green_bcm'] = profile['green_bcm']
        return config

    def __init__(self,green_bcm):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(green_bcm, GPIO.OUT)
        self.green_bcm = green_bcm
        self._pwm = GPIO.PWM(green_bcm, 70) 
        #启动pwm
        self._pwm.start(0)

    def bling(self,number=None):
        n = 0
        while  True:
            if(number is not None and n<number):
                n = n+1
            if(number is not None and n==number):
                break
            GPIO.output(self.green_bcm, GPIO.LOW) #低电平，另一端是3.3V高电平，所以点亮LED
            time.sleep(0.01) 
            GPIO.output(self.green_bcm, GPIO.HIGH) #两端都是高电平，二极管熄灭
            time.sleep(0.01)

        self.clear()

    def breath(self,number=None):
        n=0
        while True:
            if(number is not None and n<number):
                n = n+1
            if(number is not None and n==number):
                break
            for dc in range(0, 101, 1):
                self._pwm.ChangeDutyCycle(dc)
                time.sleep(0.03)
            for dc in range(100, -1, 1):
                self._pwm.ChangeDutyCycle(dc)
                time.sleep(0.03)
        self.clear()

    def clear(self):
        self._pwm.stop()
        GPIO.cleanup()


