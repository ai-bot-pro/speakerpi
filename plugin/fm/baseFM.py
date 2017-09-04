# -*- coding: utf-8-*-

import os 
import logging
import pipes
import tempfile
import subprocess

import lib.appPath
from lib.baseClass import AbstractClass

class AbstractFM(AbstractClass):
    """
    Generic parent class for FM class
    """
    @classmethod
    def is_available(cls):
        return (super(cls, cls).is_available() and
                diagnose.check_executable('mplayer'))

    def mplay(self, url):
        cmd = ['mplayer', str(url)]
        cmd_str = ' '.join([pipes.quote(arg) for arg in cmd])
        self._logger.debug('Executing %s', cmd_str)

        with tempfile.TemporaryFile() as f:
            self._mplay_process = subprocess.Popen(cmd,stdout=f,stderr=f)
            self._logger.debug("mplayer pid: '%d'", self._mplay_process.pid)
            self._mplay_process.wait()
            f.seek(0)
            output = f.read()
            if output:
                self._logger.debug("Output was: '%s'", output)

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

