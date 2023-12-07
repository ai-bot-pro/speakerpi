# -*- coding: utf-8-*-

import sys, os, time, random
import re

import yaml
import argparse
import logging
from multiprocessing import Process, Queue, Pipe
import psutil

from lib.voice.baiduVoice import BaiduVoice
from lib.voice.snowboyVoice import SnowboyVoice
from lib.mic import RawTextMic,ArecordMic,PyAudioMic
import lib.appPath
import lib.util

from plugin.fm.doubanFM import DoubanFM
import plugin.fm.doubanFM
from lib.conversation import Conversation
from plugin.bootstrap import Bootstrap
from lib.gpio.servo import Servo
from lib.gpio.led import Led
from lib.gpio.manager import Manager as gpioManager

import signal

interrupted = False

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def interrupt_callback():
    global interrupted
    return interrupted

def run(robot_name="ROBOT",logger=None,args=None):
    bootstrap_file = os.path.join(lib.appPath.CONFIG_PATH, 'bootstrap.yml')
    if os.path.exists(bootstrap_file) is False:
        logger.error("bootstrap file is not exists!")
        return False

    # Read config
    logger.debug("Trying to read config file: '%s'", bootstrap_file)
    try:
        with open(bootstrap_file, "r") as f:
            bootstrap_config = yaml.safe_load(f)
    except OSError:
        logger.error("Can't open config file: '%s'", bootstrap_file)
        raise
       
    #语音唤醒实例
    try:
        passive_stt_engine_tag = bootstrap_config['passive_stt_engine']
    except KeyError:
        passive_stt_engine_tag = 'snowboy'
        logger.warning("passive_stt_engine not specified in profile, defaulting " + "to '%s'", passive_stt_engine_tag)
    passive_stt_engine_class = lib.util.get_engine_by_tag(passive_stt_engine_tag)

    #语音识别实例
    try:
        active_stt_engine_tag = bootstrap_config['active_stt_engine']
    except KeyError:
        active_stt_engine_tag = 'baidu-ai-voice'
        logger.warning("active_stt_engine not specified in profile, defaulting " + "to '%s'", active_stt_engine_tag)
    active_stt_engine_class = lib.util.get_engine_by_tag(active_stt_engine_tag)

    #语音合成实例
    try:
        speak_engine_tag = bootstrap_config['speak_engine']
    except KeyError:
        speak_engine_tag = 'baidu-ai-voice'
        logger.warning("speak_engine not specified in profile, defaulting " + "to '%s'", speak_engine_tag)
    speak_engine_class = lib.util.get_engine_by_tag(speak_engine_tag)
    
    #语音录入实例
    passive_mic = RawTextMic() if args.debug else ArecordMic()
    active_mic = RawTextMic() if args.debug else PyAudioMic()
    
    #会话(指令)初始
    conversation = Conversation(robot_name, passive_mic, active_mic,
            speak_engine_class.get_instance(), 
            active_stt_engine_class.get_instance(),
            passive_stt_engine_class.get_instance(),
            bootstrap_config)


    #开始交互
    conversation.handleForever()

    #插件引导初始
    #bootstrap = Bootstrap(speak_engine_class.get_instance(), bootstrap_config)

    '''
    queue = Queue()
    conversation_process = Process(target=conversation.handleForever,args=(interrupt_callback,queue,))
    bootstrap_process = Process(target=bootstrap.query,args=(queue,))
    conversation_process.start()
    bootstrap_process.start()
    conversation_process.join()
    bootstrap_process.join()
    '''

def debugMic(logger,args):
    mic = ArecordMic()
    active_mic = PyAudioMic()
    passive_stt = SnowboyVoice.get_instance()
    active_stt = BaiduVoice.get_instance()
    mic.init_recording()
    while True:
        if interrupt_callback():
            logger.debug("debug mic break.")
            break
        threshold, transcribed = mic.passiveListen("weedge",
                    transcribe_callback=passive_stt.transcribe)
        if not transcribed or not threshold:
            #logger.debug("Nothing has been said or transcribed.")
            continue
        #passive_stt.play(os.path.join(lib.appPath.DATA_PATH,"snowboy/resources/ding.wav"))
        input = active_mic.activeListenToAllOptions(THRESHOLD=threshold,
                speak_callback=active_stt.play,transcribe_callback=active_stt.transcribe)
        logger.debug("input:%s",input)
        if input:
            active_stt.say(input)

    mic.terminate()

def debugLedServo(logger,args):
    print("debugLedServo")
    gpioManager.shakeshake_blingbling(process_callback=None,
                        process_args=(logger,args),
                        shake_num=1,bling_num=100)

def debugServo(logger,args):
    print("debugServo")
    Servo.get_instance().rotate(2)

def debugDaemon(logger,args):
    '''
    #daemon servo
    servo_son_processor = Process(target=lib.util.create_daemon, args=(Servo.get_instance().rotate,(1,)))
    servo_son_processor.start()
    servo_son_processor.join()
    #daemon led
    led_son_processor = Process(target=lib.util.create_daemon, args=(Led.get_instance().bling,(100,)))
    led_son_processor.start()
    led_son_processor.join()
    time.sleep(30)
    '''
    print("debug daemon servo ")
    lib.util.create_daemon(daemon_callback=debugServo,args=(logger,args))
    print("debug daemon over")

def debugLed(logger,args):
    print("debugLed")
    print("-----led bling----")
    Led.get_instance().bling(10)
    print("-----led breath----")
    Led.get_instance().breath(10)


if __name__ == '__main__':
    # capture SIGINT signal, e.g., Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description='doubanFM pi')
    parser.add_argument('--debug', action='store_true',
                        help='Show debug messages')
    parser.add_argument('--debugDoubanFmPlugin', action='store_true',
                        help='Show debug douban fm plugin messages')
    parser.add_argument('--debugLed', action='store_true',
                        help='Show debug gpio led messages')
    parser.add_argument('--debugServo', action='store_true',
                        help='Show debug gpio servo messages')
    parser.add_argument('--debugLedServo', action='store_true',
                        help='Show debug gpio servo messages')
    parser.add_argument('--debugDaemon', action='store_true',
                        help='Show debug create daemon porcessor messages')
    parser.add_argument('--debugMic', action='store_true',
                        help='Show debug mic messages')

    args = parser.parse_args()
    
    logging.basicConfig(stream=sys.stdout)
    logger = logging.getLogger("")
    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.debugMic:
        debugMic(logger,args)
        exit()

    if args.debugDaemon:
        debugDaemon(logger,args)
        exit()

    if args.debugLedServo:
        debugLedServo(logger,args)
        exit()

    if args.debugServo:
        debugServo(logger,args)
        exit()

    if args.debugLed:
        debugLed(logger,args)
        exit()

    if args.debugDoubanFmPlugin:
        debugDoubanFm(logger,args)
        exit()

    run('weedge',logger,args)


