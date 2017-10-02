# -*- coding: utf-8-*-

import os
import logging
import pipes
import tempfile
import subprocess
import psutil
import signal
from abc import ABCMeta, abstractmethod

import yaml

import lib.diagnose
import lib.appPath

class AbstractVoiceEngine(object):
    """
    Generic parent class for voice engine class
    """
    __metaclass__ = ABCMeta

    @classmethod
    def get_config(cls):
        return {}

    @classmethod
    def get_instance(cls):
        config = cls.get_config()
        instance = cls(**config)
        return instance

    @classmethod
    @abstractmethod
    def is_available(cls):
        return lib.diagnose.check_executable('play')

    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)

        config_path = os.path.join(lib.appPath.CONFIG_PATH, 'log.yml');
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                profile = yaml.safe_load(f)
                if 'level' in profile:
                    self._logger.setLevel(eval("logging."+profile['level']))

    @abstractmethod
    def say(self, phrase):
        self._logger.info("Saying '%s' with dummy speaker", phrase)
        pass

    @abstractmethod
    def transcribe(self, fp):
        pass

    def play(self, filename,tag=None):
        '''
        tag: 给调用播放语音的speaker进程打个标签
        '''
        cmd = ['play', str(filename)]
        self._logger.debug('Executing %s', ' '.join([pipes.quote(arg)
                                                     for arg in cmd]))
        with tempfile.TemporaryFile() as f:
            self._play_process = subprocess.Popen(cmd,stdout=f,stderr=f,preexec_fn=os.setsid)
            self._logger.debug("play pid: '%d'", self._play_process.pid)

            pid_name = self.__class__.__name__+"_"+tag+"_play.pid" if tag is not None else self.__class__.__name__+"_play.pid"
            pid_file = os.path.join(lib.appPath.DATA_PATH,pid_name)
            with open(pid_file, 'w') as pid_fp:
                pid_fp.write(str(self._play_process.pid))
                pid_fp.close()

            self._play_process.wait()

            #播放完删除
            if os.path.exists(pid_file):
                os.remove(pid_file)

            f.seek(0)
            output = f.read()
            if output:
                self._logger.debug("Output was: '%s'", output)

    def kill_play_procsss(self,tag=None):
        pid_name = self.__class__.__name__+"_"+tag+"_play.pid" if tag is not None else self.__class__.__name__+"_play.pid"
        pid_file = os.path.join(lib.appPath.DATA_PATH,pid_name)
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read())
                f.close()
                if pid: 
                    self._logger.debug("pgkill play pid: %d",pid)
                    os.killpg(pid,signal.SIGKILL)

    def suspend_play_process(self,tag=None):
        res = None
        pid_name = self.__class__.__name__+"_"+tag+"_play.pid" if tag is not None else self.__class__.__name__+"_play.pid"
        pid_file = os.path.join(lib.appPath.DATA_PATH,pid_name)
        with open(pid_file, 'r') as f:
            pid = int(f.read())
            f.close()
            if pid: 
                self._logger.debug("suspend play pid: %d",pid)
                res = psutil.Process(pid).suspend()
        return res

    def resume_play_process(self,tag=None):
        pid_name = self.__class__.__name__+"_"+tag+"_play.pid" if tag is not None else self.__class__.__name__+"_play.pid"
        pid_file = os.path.join(lib.appPath.DATA_PATH,pid_name)
        with open(pid_file, 'r') as f:
            pid = int(f.read())
            f.close()
            if pid: 
                self._logger.debug("resume play pid: %d",pid)
                res = psutil.Process(pid).resume()
        return res
