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
        self.on_state = GPIO.HIGH
        self.off_state = not self.on_state

    def get_bcm_port(self):
        return self.green_bcm
    def set_on(self):
        GPIO.output(self.green_bcm, self.on_state)
    def set_off(self):
        GPIO.output(self.green_bcm, self.off_state)
    def is_on(self):
        return GPIO.input(self.green_bcm) == self.on_state
    def is_off(self):
        return GPIO.input(self.green_bcm) == self.off_state
    def toggle(self):
        if self.is_on():
            self.set_off()
        else:
            self.set_on()

    def blink(self, t=0.3):
        self.set_off()
        self.set_on()
        time.sleep(t)
        self.set_off()

    def bling(self,number=None):
        n = 0
        while  True:
            if(number is not None and n<number):
                n = n+1
            if(number is not None and n==number):
                break
            self.blink()
            time.sleep(0.7)

        GPIO.cleanup()

    def breath(self,number=None):
        pwm = GPIO.PWM(self.green_bcm, 70) 
        pwm.start(0)
        n=0
        while True:
            if(number is not None and n<number):
                n = n+1
            if(number is not None and n==number):
                break
            for dc in range(0, 101, 1):
                pwm.ChangeDutyCycle(dc)
                time.sleep(0.03)
            for dc in range(100, -1, 1):
                pwm.ChangeDutyCycle(dc)
                time.sleep(0.03)
        pwm.stop()
        GPIO.cleanup()


