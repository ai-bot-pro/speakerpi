#!/usr/bin/env python
# -*- coding: utf-8 -*-
from multiprocessing import Pipe, Process
import os, time, random


def son_process(x, from_pipe,to_pipe,block=False):
    _out_from_pipe, _in_from_pipe = from_pipe
    _out_to_pipe, _in_to_pipe = to_pipe

    _in_from_pipe.close()
    _out_to_pipe.close()
    while True:
        try:
            print("coprocess recv msg from from_pipe")
            if block==True:
                msg = _out_from_pipe.recv()
            else:
                msg = None
                if _out_from_pipe.poll():
                    msg = _out_from_pipe.recv()
            print msg
            print("coprocess recv msg from from_pipe end")
            if msg == 1:
                time.sleep(10)
                print("--coprocess send msg is begin--")
                _in_to_pipe.send("get msg:"+str(msg))
                print("--coprocess send msg is over--")
        except EOFError:
            # 当out_from_pipe接受不到输出的时候且输入被关闭的时候，会抛出EORFError，可以捕获并且退出子进程
            print("---break---")
            break


if __name__ == '__main__':
    out_from_pipe, in_from_pipe = Pipe(True)
    out_to_pipe, in_to_pipe = Pipe(True)
    #coprocess 协同进程
    son_p = Process(target=son_process, args=(100, (out_from_pipe, in_from_pipe),(out_to_pipe,in_to_pipe),True))
    son_p.start()
    # 等from_pipe被fork 后，关闭主进程的输出端
    # 创建的Pipe一端连接着主进程的输入，一端连接着子进程的输出口
    out_from_pipe.close()
    # 等to_pipe被fork 后，关闭主进程的输入端
    # 创建的Pipe一端连接着主进程的输出，一端连接着子进程的输入口
    in_to_pipe.close()
    #while True:
    print "--send begin--"
    for x in range(11):
        in_from_pipe.send(x)
    print("--send is over--")

    msg = out_to_pipe.recv()
    print("recv msg { %s } from to_pipe"%msg)

    in_from_pipe.close()
    out_to_pipe.close()
    son_p.join()
    print "子进程结束了"
