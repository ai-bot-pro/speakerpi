# -*- coding: utf-8-*-
import sys
import os
import json
import requests
import tempfile

import yaml

import lib.diagnose
import lib.appPath
from lib.baseClass import AbstractClass

try:
    from aip import AipImageClassify
    from aip import AipFace
except ImportError:
    pass

class BaiduGraphic(AbstractClass):
    """
    Uses the Baidu AI Cloud Services.
    """
    TAG = "baidu-ai-image"

    def __init__(self, app_id='', api_key='', secret_key=''):
        super(self.__class__, self).__init__()
        self._aipImageClassify = AipImageClassify(app_id, api_key, secret_key)
        self._aipFace = AipFace(app_id, api_key, secret_key)

    @classmethod
    def get_config(cls):
        config = {}
        config_path = os.path.join(lib.appPath.CONFIG_PATH, 'baidu.yml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                profile = yaml.safe_load(f)
                if 'image' in profile:
                    image_config = profile['image']
                    if 'app_id' in image_config:
                        config['app_id'] = image_config['app_id']
                    if 'api_key' in image_config:
                        config['api_key'] = image_config['api_key']
                    if 'secret_key' in image_config:
                        config['secret_key'] = image_config['secret_key']
        return config

    @classmethod
    def is_available(cls):
        return (super(cls, cls).is_available() and
                lib.diagnose.check_python_import('aip') and
                lib.diagnose.check_network_connection('www.baidu.com'))

    def detectImage(self,image,detect_type="object",options=None):
        res = None
        detector= {
            "object": self._aipImageClassify.objectDetect,
            "dish": self._aipImageClassify.dishDetect,
            "car": self._aipImageClassify.carDetect,
            "logo": self._aipImageClassify.logoSearch,
            "animal": self._aipImageClassify.animalDetect,
            "plant": self._aipImageClassify.plantDetect,
            "face": self._aipFace.detect,
        }

        if detector.has_key(detect_type):
            if options is not None and type(options) is dict:
                res = detector[detect_type](image,options)
            else:
                res = detector[detect_type](image)
            self._logger.debug("detect %s result: %s",detect_type,json.dumps(res,encoding="UTF-8",ensure_ascii=False))
            if("error_code" in res):
                self._logger.warning("detect %s error: %s - %s",detect_type,res['error_code'],res['error_msg'])
                return None
            if(type(res['result']) is dict):
                return res['result']
            if(len(res['result'])>0 and type(res['result']) is list):
                res = res['result'][0]
        return res

