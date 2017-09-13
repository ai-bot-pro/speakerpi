#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys,os,time
from multiprocessing import Process, Queue, Pipe
from lib.gpio.servo import Servo
from lib.gpio.led import Led

class Manager:

    def __init__(self):
        pass

    @classmethod
    def sharkshark_blingbling(cls,process_callback=None,process_args=(),shark_num=2,bling_num=2):
        '''
        process_callback: 主程序处理逻辑函数，
        process_args: 主程序函数需要的参数，tuple
        shark_num: 摇摆的次数，这个次数最好是根据主程序的处理时间而定，摆动一次大概1s左右,具体由ratate函数决定
        bling_num: led灯闪烁的次数，这个次数最好是根据主程序的处理时间而定，bling一次大概<0.01s左右,具体由bling函数决定
        '''
        if(type(process_args) is not tuple):
            print("process_callback function's args is tuple type")
            return False
        if(shark_num>0):
            print("sharkshark")
            servo_son_processor = Process(target=Servo.get_instance().rotate, args=(shark_num,))
            servo_son_processor.start()
        if(bling_num>0):
            print("blingbling")
            led_son_processor = Process(target=Led.get_instance().bling, args=(bling_num,))
            led_son_processor.start()

        if process_callback is not None:
             process_callback(*process_args)
        
        if(shark_num>0):
            servo_son_processor.join()
        if(bling_num>0):
            led_son_processor.join()

    @classmethod
    def sharkshark(cls,son_process_callback=None,process_args=(),shark_num=1):
        son_processor = Process(target=son_process_callback, args=process_args)
        son_processor.start()
        if(shark_num>0):
            print("sharkshark~, only you~~~~!  just only u~~~")
            Servo.get_instance().rotate(shark_num)
        son_processor.join()

