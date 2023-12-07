# -*- coding: utf-8-*-

import os 
from abc import ABCMeta, abstractmethod

import lib.appPath
import lib.util

class AbstractClass(object):
    """
    Generic parent class for all class
    """
    __metaclass__ = ABCMeta

    @classmethod
    def get_config(cls):
        return {}

    """
    __init__ params'name must be the same with config
    """
    @classmethod
    def get_instance(cls):
        config = cls.get_config()
        instance = cls(**config)
        return instance

    @classmethod
    @abstractmethod
    def is_available(cls):
        return true

    def __init__(self, **kwargs):
        self._logger = lib.util.init_logger(__name__)

