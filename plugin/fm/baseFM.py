# -*- coding: utf-8-*-

import os 
import logging
import pipes
import tempfile
import subprocess
import psutil
import signal

import lib.appPath
from lib.baseClass import AbstractClass

class AbstractFM(AbstractClass):
    """
    Generic parent class for FM class
    """
    @classmethod
    def is_available(cls):
        return (super(cls, cls).is_available() and
                lib.diagnose.check_executable('mplayer'))

    def mplay(self, url):
        cmd = ['mplayer', str(url)]
        cmd_str = ' '.join([pipes.quote(arg) for arg in cmd])
        self._logger.debug('Executing %s', cmd_str)

        with tempfile.TemporaryFile() as f:
            self._mplay_process = subprocess.Popen(cmd,stdout=f,stderr=f,preexec_fn=os.setsid)
            self._logger.debug("mplayer pid: '%d'", self._mplay_process.pid)

            #正在播放的时候保存mplayer pid（这个pid为进程组id)
            pid_file = os.path.join(lib.appPath.DATA_PATH,self.__class__.__name__+"_mplay.pid")
            with open(pid_file, 'w') as pid_fp:
                pid_fp.write(str(self._mplay_process.pid))
                pid_fp.close()
            
            self._mplay_process.wait()

            #播放完删除mplayer pid 文件
            if os.path.exists(pid_file):
                os.remove(pid_file)

            f.seek(0)
            output = f.read()
            if output:
                self._logger.debug("Output was: '%s'", output)

    @classmethod
    def kill_mplay_procsss(cls):
        '''
        kill当前播放的mplay进程 （进程id从文件中获取）
        '''
        pid_file = os.path.join(lib.appPath.DATA_PATH,cls.__name__+"_mplay.pid")
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read())
                print("-----")
                print(pid_file,pid)
                print("-----")
                f.close()
                if pid: 
                    print("pgkill mplay pid: %d"%pid)
                    os.killpg(pid,signal.SIGKILL)
    
    @classmethod
    def suspend_mplay_process(cls):
        '''
        挂起当前播放的mplay进程 （进程id从文件中获取）
        '''
        res = None
        pid_file = os.path.join(lib.appPath.DATA_PATH,cls.__name__+"_mplay.pid")
        with open(pid_file, 'r') as f:
            pid = int(f.read())
            print("---suspend--")
            print(pid_file,pid)
            print("-----")
            f.close()
            if pid: 
                print("suspend mplay pid: %d"%pid)
                res = psutil.Process(pid).suspend()
        return res
    
    @classmethod
    def resume_mplay_process(cls):
        '''
        唤醒当前播放的mplay进程 （进程id从文件中获取）
        '''
        pid_file = os.path.join(lib.appPath.DATA_PATH,cls.__name__+"_mplay.pid")
        with open(pid_file, 'r') as f:
            pid = int(f.read())
            print("---resume--")
            print(pid_file,pid)
            print("-----")
            f.close()
            if pid: 
                print("resume mplay pid: %d"%pid)
                res = psutil.Process(pid).resume()
        return res

    def login(self):
        pass

    def getAccessToken(self):
        pass

    def getSong(self):
        pass

    def setLikeSong(self):
        pass

    def setUnLikeSong(self):
        pass

    def setHateSong(self):
        pass

    def downloadSong(self):
        pass

    def next(self):
        pass

    def stop(self):
        pass

    def play(self):
        pass

