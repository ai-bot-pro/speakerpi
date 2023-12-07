# -*- coding: utf-8-*-
import sys, os, time, random

import lib.util
from plugin.bootstrap import Bootstrap
from lib.gpio.manager import Manager as gpioManager

class Conversation(object):
    """
    会话交互
    """
    def __init__(self, robot_name, passive_mic,active_mic,
            speaker, active_stt, passive_stt, bootstrap_config):
        self._logger = lib.util.init_logger(__name__)
        self.robot_name = robot_name
        self.passive_mic = passive_mic
        self.active_mic = active_mic
        self.speaker = speaker
        self.active_stt = active_stt
        self.passive_stt = passive_stt
        try:
            ai_chat_engine = bootstrap_config['ai_chat_engine']
            self.ai_chat  = lib.util.get_engine_by_tag(ai_chat_engine,cate="aiChat").get_instance()
        except KeyError:
            self.ai_chat = None
        self.bootstrap_config = bootstrap_config
        self.bootstrap = Bootstrap(speaker, self.ai_chat, bootstrap_config)

    def handleForever(self,interrupt_check=None,queue=None):
        self._logger.info("开始和机器人{ %s }会话", self.robot_name)
        init_talk_text = "hi,您好,我叫" + self.robot_name + ",很高兴认识你,您可以叫我名字唤醒我"

        if('robot_open_shake_bling' in self.bootstrap_config
                and self.bootstrap_config['robot_open_shake_bling']=="yes"):
            #会话开始 shake shake
            gpioManager.shakeshake(
                son_process_callback=self.speaker.say,
                process_args=(init_talk_text,),
                shake_num=1)
        else:
            self.speaker.say(init_talk_text)

        '''
        两种语音录入方式(命令arecord方式; 利用pyaudio库。默认频率16000Hz)
        暂时使用时，用arecord方式录入唤醒词识别，用pyaudio库来录入正式会话内容
        @todo: 使用arecord方式来录入正式会话内容,以及优化用pyaudio库的方式
        '''
        self.passive_mic.init_recording()
        while True:
            if interrupt_check is not None:
                if interrupt_check():
                    break

            threshold, transcribed = self.passive_mic.passiveListen(self.robot_name,
                    transcribe_callback=self.passive_stt.transcribe)

            if not transcribed or not threshold:
                continue
            self._logger.info("Keyword '%s' has been said!", self.robot_name)

            self._logger.debug("Started to listen actively with threshold: %r", threshold)
            input = self.active_mic.activeListenToAllOptions(threshold,
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
                    ok = self.bootstrap.query(input)
                    #没有命中本地指令，进入聊天模式
                    if ok is False and self.ai_chat is not None:
                        stream = self.ai_chat.stream_chat(input) 
                        self.speaker.stream_say(stream)
            else:
                self.speaker.say("没听清楚您说什么")

        self.passive_mic.terminate()
