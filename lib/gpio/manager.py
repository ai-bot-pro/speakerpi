#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys,os,time
from multiprocessing import Process, Queue, Pipe

import lib.appPath
from lib.gpio.servo import Servo
from lib.gpio.led import Led

class Manager:

    def __init__(self):
        pass

    @classmethod
    def shakeshake_blingbling(cls,tag,process_callback=None,process_args=(),shake_num=2,bling_num=2):
        '''
        tag: 必须参数，用于区分不同调用方产生的子进程
        process_callback: 主程序处理逻辑函数，
        process_args: 主程序函数需要的参数，tuple
        shake_num: 摇摆的次数，这个次数最好是根据主程序的处理时间而定，摆动一次大概1s左右,具体由ratate函数决定
        bling_num: led灯闪烁的次数，这个次数最好是根据主程序的处理时间而定，bling一次大概1s左右,具体由bling函数决定
        '''
        if(type(process_args) is not tuple):
            print("process_callback function's args is tuple type")
            return False
        if(shake_num>0):
            print("shakeshake")
            servo = Servo.get_instance()
            servo_son_processor = Process(target=servo.rotate, args=(shake_num,))
            servo_pid_file = os.path.join(lib.appPath.DATA_PATH,tag+"_"+str(servo.get_bcm_port())+"_servo.pid")
            with open(servo_pid_file, 'w') as pid_fp:
                pid_fp.write(str(servo_son_processor.pid))
                pid_fp.close()
            servo_son_processor.start()
        if(bling_num>0):
            print("blingbling")
            led = Led.get_instance()
            led_son_processor = Process(target=led.bling, args=(bling_num,))
            led_pid_file = os.path.join(lib.appPath.DATA_PATH,tag+"_"+str(led.get_bcm_port())+"_led.pid")
            with open(led_pid_file, 'w') as pid_fp:
                pid_fp.write(str(led_son_processor.pid))
                pid_fp.close()
            led_son_processor.start()

        if process_callback is not None:
            process_callback(*process_args)
        
        if(shake_num>0):
            servo_son_processor.join()
            if os.path.exists(servo_pid_file):
                os.remove(servo_pid_file)
        if(bling_num>0):
            led_son_processor.join()
            if os.path.exists(led_pid_file):
                os.remove(led_pid_file)

    @classmethod
    def shakeshake(cls,son_process_callback=None,process_args=(),shake_num=1):
        son_processor = Process(target=son_process_callback, args=process_args)
        son_processor.start()
        if(shake_num>0):
            print("shakeshake~, only you~~~~!  just only u~~~")
            Servo.get_instance().rotate(shake_num)
        son_processor.join()

    @classmethod
    def kill_procsss(cls,tag):
        '''
        kill当前播放的进程 （进程id从文件中获取）
        '''
        def kill_pid(pid_file,tag):
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    pid = int(f.read())
                    print("-----")
                    print(pid_file,pid)
                    print("-----")
                    f.close()
                    if pid: 
                        print("kill "+tag+" pid: %d"%pid)
                        os.kill(pid,signal.SIGKILL)
        led = Led.get_instance()
        servo = Servo.get_instance()
        led_pid_file = os.path.join(lib.appPath.DATA_PATH,tag+"_"+led.get_bcm_port()+"_led.pid")
        kill_pid(led_pid_file)
        servo_pid_file = os.path.join(lib.appPath.DATA_PATH,tag+"_"+servo.get_bcm_port()+"_servo.pid")
        kill_pid(servo_pid_file)
    
    @classmethod
    def suspend_process(cls,tag):
        '''
        挂起当前gpio进程 （进程id从文件中获取）
        '''
        def suspend(pid_file):
            res = None
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    pid = int(f.read())
                    print("---suspend--")
                    print(pid_file,pid)
                    print("-----")
                    f.close()
                    if pid: 
                        print("suspend  pid: %d"%pid)
                        res = psutil.Process(pid).suspend()
            return res

        pid_file = os.path.join(lib.appPath.DATA_PATH,tag+"led_.pid")
        res1 = suspend(pid_file)
        pid_file = os.path.join(lib.appPath.DATA_PATH,tag+"servo_.pid")
        res2 = suspend(pid_file)
        return res1 or res2
    
    @classmethod
    def resume_process(cls,tag):
        '''
        唤醒当前gpio进程 （进程id从文件中获取）
        '''
        def resume(pid_file):
            res = None
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    pid = int(f.read())
                    print("---resume--")
                    print(pid_file,pid)
                    print("-----")
                    f.close()
                    if pid: 
                        print("resume  pid: %d"%pid)
                        res = psutil.Process(pid).resume()
            return res
        pid_file = os.path.join(lib.appPath.DATA_PATH,tag+"led_.pid")
        res1 = resume(pid_file)
        pid_file = os.path.join(lib.appPath.DATA_PATH,tag+"led_.pid")
        res2 = resume(pid_file)

        return res1 or res2
