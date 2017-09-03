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
    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.INFO)

    @classmethod
    def is_available(cls):
        return super(cls, cls).is_available() 

    def mplay(self, url):
        cmd = ['mplayer', str(url)]
        self._logger.debug('Executing %s', ' '.join([pipes.quote(arg) for arg in cmd]))

        with tempfile.TemporaryFile() as f:
            subprocess.call(cmd, stdout=f, stderr=f)
            f.seek(0)
            output = f.read()
            if output:
                self._logger.debug("Output was: '%s'", output)

    @classmethod
    def login(self):
        pass

    @classmethod
    def getAccessToken(self):
        pass

    @classmethod
    def getSong(self):
        pass

    @classmethod
    def setLikeSong(self):
        pass

    @classmethod
    def setUnLikeSong(self):
        pass

    @classmethod
    def setHateSong(self):
        pass

    @classmethod
    def downloadSong(self):
        pass

    @classmethod
    def next(self):
        pass

    @classmethod
    def stop(self):
        pass

    @classmethod
    def play(self):
        pass

