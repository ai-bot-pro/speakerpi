# -*- coding: utf-8-*-

import logging

from abc import ABCMeta, abstractmethod

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
        self._logger = logging.getLogger(__name__)
