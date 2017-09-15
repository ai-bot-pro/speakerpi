#!/usr/bin/env python
# -*- coding: utf-8 -*-
# look this: http://www.toptechboy.com/raspberry-pi/raspberry-pi-lesson-28-controlling-a-servo-on-raspberry-pi-with-python/
import sys,os,time
import logging
import yaml

import RPi.GPIO as GPIO

import lib.appPath
from lib.baseClass import AbstractClass

class Servo(AbstractClass):

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
                if 'servo' in profile:
                    profile = profile['servo']
                    if 'bcm' in profile:
                        config['bcm'] = profile['bcm']
        return config
    
    def __init__(self,bcm):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(bcm, GPIO.OUT)
        self.bcm = bcm
        self._pwm = GPIO.PWM(bcm, 50) 
        self._pwm.start(7)

    def get_bcm_port():
        return self.bcm

    def rotate(self,number=1):
        for n in range(0,number):
            for dc in range(0, 180, 1):
                dc = 1./18.*dc + 2
                self._pwm.ChangeDutyCycle(dc)
                time.sleep(0.01)
            for dc in range(180, 0, -1):
                dc = 1./18.*dc + 2
                self._pwm.ChangeDutyCycle(dc)
                time.sleep(0.01)

        self.clear()

    def clear(self):
        self._pwm.stop()
        GPIO.cleanup()


