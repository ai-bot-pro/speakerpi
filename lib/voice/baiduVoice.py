# -*- coding: utf-8-*-

import sys
import os
import json
import requests
import tempfile

import yaml

import lib.diagnose
from baseVoice import AbstractVoiceEngine
import lib.appPath

try:
    from aip import AipSpeech
except ImportError:
    pass

class BaiduVoice(AbstractVoiceEngine):
    """
    Uses the Baidu AI Cloud Services.
    """
    TAG = "baidu-ai-voice"

    def __init__(self, app_id='', api_key='', secret_key='',
            per=0, output_file=os.path.join(lib.appPath.DATA_PATH, 'baidu_voice.mp3')):
        super(self.__class__, self).__init__()
        self._aipSpeech = AipSpeech(app_id, api_key, secret_key)
        self._per = per
        self._output_file = output_file

    @classmethod
    def get_config(cls):
        config = {}
        config_path = os.path.join(lib.appPath.CONFIG_PATH, 'baidu.yml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                profile = yaml.safe_load(f)
                if 'voice' in profile:
                    voice_config = profile['voice']
                    if 'app_id' in voice_config:
                        config['app_id'] = voice_config['app_id']
                    if 'api_key' in voice_config:
                        config['api_key'] = voice_config['api_key']
                    if 'secret_key' in voice_config:
                        config['secret_key'] = voice_config['secret_key']
                    if 'per' in voice_config:
                        config['per'] = voice_config['per']
                    if 'output_file' in voice_config:
                        config['output_file'] = voice_config['output_file']
        return config

    @classmethod
    def is_available(cls):
        return (super(cls, cls).is_available() and
                lib.diagnose.check_python_import('aip') and
                lib.diagnose.check_network_connection('www.baidu.com'))

    def say(self, phrase):
        if not phrase: return False
        self._logger.debug("Saying '%s' with '%s'", phrase, self.TAG)
        result  = self._aipSpeech.synthesis(phrase, 'zh', 1, { 'per':self._per,'vol': 5, })
        # 识别正确返回语音二进制 错误则返回dict 参照http://yuyin.baidu.com/docs/tts/196 错误码
        if not isinstance(result, dict):
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                f.write(result)
                tmpfile = f.name
                #使用临时文件创建，防止多个进程操作一个文件
                self.play(tmpfile)
                os.remove(tmpfile)
        else:
            self._logger.debug("TTS service response[ %s ] with '%s'", json.dumps(result), self.TAG)

    def transcribe(self,fp):
        fp.seek(0)
        records = fp.read()
        dict_data = self._aipSpeech.asr(records, 'wav', 16000, { 'lan': 'zh', })
        self._logger.debug('baidu stt response: %s',json.dumps(dict_data))
        transcribed = []
        if 'result' in dict_data:
            text = dict_data['result'][0].encode('utf-8')
            transcribed.append(text)
            self._logger.info('百度语音识别到了: %s', text)
        return transcribed

