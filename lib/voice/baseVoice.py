# -*- coding: utf-8-*-

import logging
import pipes
import tempfile
import subprocess
from abc import ABCMeta, abstractmethod

import lib.diagnose

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
        return diagnose.check_executable('play')

    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.INFO)

    @abstractmethod
    def say(self, phrase, *args):
        pass

    def play(self, filename):
        cmd = ['play', str(filename)]
        self._logger.debug('Executing %s', ' '.join([pipes.quote(arg)
                                                     for arg in cmd]))
        with tempfile.TemporaryFile() as f:
            subprocess.call(cmd, stdout=f, stderr=f)
            f.seek(0)
            output = f.read()
            if output:
                self._logger.debug("Output was: '%s'", output)

