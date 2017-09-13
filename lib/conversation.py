# -*- coding: utf-8-*-
import sys, os, time, random
import lib.util
from plugin.bootstrap import Bootstrap
from lib.gpio.manager import Manager as gpioManager

import signal

interrupted = False

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def interrupt_callback():
    global interrupted
    return interrupted

# capture SIGINT signal, e.g., Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

class Conversation(object):
    """
    会话交互
    """
    def __init__(self, robot_name, mic,
            speaker, active_stt, passive_stt, bootstrap_config):
        self._logger = lib.util.init_logger(__name__)
        self.robot_name = robot_name
        self.mic = mic
        self.speaker = speaker
        self.active_stt = active_stt
        self.passive_stt = passive_stt
        self.bootstrap_config = bootstrap_config
        self.bootstrap = Bootstrap(speaker, bootstrap_config)

    def handleForever(self,interrupt_check=interrupt_callback,queue=None):
        self._logger.info("开始和机器人{ %s }会话", self.robot_name)
        init_talk_text = "hi,您好,我叫" + self.robot_name + ",很高兴认识你,您可以叫我名字唤醒我"

        if('robot_open_shark_bling' in self.bootstrap_config
                and self.bootstrap_config['robot_open_shark_bling']=="yes"):
            #会话开始 shark shark
            gpioManager.sharkshark(
                son_process_callback=self.speaker.say,
                process_args=(init_talk_text,),
                shark_num=1)
        else:
            self.speaker.say()

        while True:
            if interrupt_check is not None:
                if interrupt_check(): 
                    break

            self._logger.debug("Started to listen kw : %s", self.robot_name)
            threshold, transcribed = self.mic.passiveListen(self.robot_name,
                    transcribe_callback=self.passive_stt.transcribe)
            self._logger.debug("Stop to listen kw : %s", self.robot_name)

            if not transcribed or not threshold:
                self._logger.info("Nothing has been said or transcribed.")
                continue
            self._logger.info("Keyword '%s' has been said!", self.robot_name)

            self._logger.debug("Started to listen actively with threshold: %r", threshold)
            input = self.mic.activeListenToAllOptions(threshold,
                    speak_callback=self.speaker.play,
                    transcribe_callback=self.active_stt.transcribe)
            self._logger.debug("Stopped to listen actively with threshold: %r and input: %s", threshold, input)
            if input :
                if queue is not None:
                    #将识别的指令发到Queue中，由其他进程处理
                    # (todo:由bootstrap引导进程处理,通过pipe分发给plugin进程,
                    #  前提需要一个daemon进程fork2个进程:1.conversation会话进程，2.bootstrap引导进程)
                    queue.put(input)
                else:
                    #直接将识别的指令发给bootstrap引导模块处理
                    self.bootstrap.query(input)
            else:
                self.speaker.say("没听清楚，请再说一次")
