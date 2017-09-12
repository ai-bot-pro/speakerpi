#!/usr/bin/env python
# -*- coding: utf-8 -*-
from multiprocessing import Pipe, Process
import os, time, random


def son_process(x, pipe,block=False):
    _out_pipe, _in_pipe = pipe

    # 关闭fork过来的输入端
    _in_pipe.close()
    while True:
        try:
            print("recv msg from pipe")
            if block==True:
                msg = _out_pipe.recv()
            else:
                msg = None
                if _out_pipe.poll():
                    msg = _out_pipe.recv()
            print("recv msg from pipe end")
            print msg
        except EOFError:
            # 当out_pipe接受不到输出的时候且输入被关闭的时候，会抛出EORFError，可以捕获并且退出子进程
            print("---break---")
            break


if __name__ == '__main__':
    out_pipe, in_pipe = Pipe(True)
    son_p = Process(target=son_process, args=(100, (out_pipe, in_pipe),False))
    son_p.start()
    # 等pipe被fork 后，关闭主进程的输出端
    # 这样，创建的Pipe一端连接着主进程的输入，一端连接着子进程的输出口
    out_pipe.close()
    time.sleep(3)
    while True:
        print "try agian"
        for x in range(11):
            if x==1:
                time.sleep(123)
            else:
                if x==10:
                    #print "in_pipe.close()"
                    #in_pipe.close()
                    #print "join"
                    #son_p.join()
                    print "子进程结束了"
                    time.sleep(10)
                else:
                    in_pipe.send(x)

