# -*- coding: utf-8-*-

import sys
import os
import time

import yaml

import lib.diagnose
from baseVoice import AbstractVoiceEngine
import lib.appPath

from lib.voice.snowboy import snowboydetect

class SnowboyVoice(AbstractVoiceEngine):
    """
    Uses the snowboy hotword detector 
    """
    TAG = "snowboy"

    def __init__(self, decoder_model,
                 resource=os.path.join(lib.appPath.DATA_PATH, "snowboy/resources/common.res"),
                 sensitivity=[],
                 hotwords=[]):
        super(self.__class__, self).__init__()

        self.hotwords = hotwords
        tm = type(decoder_model)
        ts = type(sensitivity)
        if tm is not list:
            decoder_model = [decoder_model]
        if ts is not list:
            sensitivity = [sensitivity]
        model_str = ",".join(decoder_model)

        self.detector = snowboydetect.SnowboyDetect(
            resource_filename=resource.encode(), model_str=model_str.encode())
        self.detector.SetAudioGain(1)
        self.num_hotwords = self.detector.NumHotwords()

        if len(decoder_model) > 1 and len(sensitivity) == 1:
            sensitivity = sensitivity*self.num_hotwords
        if len(sensitivity) != 0:
            assert self.num_hotwords == len(sensitivity), \
                "number of hotwords in decoder_model (%d) and sensitivity " \
                "(%d) does not match" % (self.num_hotwords, len(sensitivity))
        sensitivity_str = ",".join([str(t) for t in sensitivity])
        if len(sensitivity) != 0:
            self.detector.SetSensitivity(sensitivity_str.encode())

    @classmethod
    def get_config(cls):
        config = {}
        config_path = os.path.join(lib.appPath.CONFIG_PATH, 'snowboy.yml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                profile = yaml.safe_load(f)
                if 'hotwords' in profile:
                    config['hotwords'] = profile['hotwords'].split(',');
                if 'sensitivity' in profile:
                    config['sensitivity'] = profile['sensitivity'].split(',');
                if 'decoder_model' in profile:
                    config['decoder_model'] = profile['decoder_model'].split(',');
        return config

    @classmethod
    def is_available(cls):
        return (super(cls, cls).is_available() and
                lib.diagnose.check_python_import('lib.voice.snowboy.snowboydetect'))

    def say(self, phrase, cache=None):
        pass

    def transcribe(self,fp):
        if(type(fp) is str):
            data = fp
        else:
            fp.seek(44)
            data = fp.read()
        ans = self.detector.RunDetection(data)
        if ans == -1:
            self._logger.warning("Error initializing streams or reading audio data")
        if ans > 0:
            message = "Keyword " + str(ans) + " detected at time: "
            message += time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            message += " with " + self.TAG
            self._logger.info(message)
            return [self.hotwords[ans-1].encode('UTF-8')]
        else:
            return []

