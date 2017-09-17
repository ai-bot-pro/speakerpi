# -*- coding: utf-8-*-
# from jasper mic.py change sm
import os,time
import tempfile
import logging
import audioop
import pyaudio
import collections
import wave
import subprocess
import threading

import lib.util
import lib.appPath

class RingBuffer(object):
    """Ring buffer to hold audio from audio capturing tool"""
    def __init__(self, size = 4096):
        self._buf = collections.deque(maxlen=size)

    def extend(self, data):
        """Adds data to the end of buffer"""
        self._buf.extend(data)

    def get(self):
        """Retrieves data from the beginning of buffer and clears it"""
        tmp = bytes(bytearray(self._buf))
        self._buf.clear()
        return tmp


class MicWrapper:
    '''
    just a wrapper,just nothing todo
    '''
    def __init__(self):
        pass

    def passiveListen(self, detected_word, 
            transcribe_callback=None,type="arecord"):
        if(type=="pyaudio"):
            mic = PyAudioMic()
            return mic.passiveListen(detected_word, transcribe_callback)
        if(type=="rawtext"):
            mic = RawTextMic()
            return mic.passiveListen(detected_word, transcribe_callback)

        mic = ArecordMic()
        return mic.passiveListen(detected_word, transcribe_callback)

    def activeListenToAllOptions(self, THRESHOLD=None, speak_callback=None,
            transcribe_callback=None, type="pyaudio"):
        if(type=="pyaudio"):
            mic = PyAudioMic()
            return mic.activeListenToAllOptions(THRESHOLD,speak_callback)
        if(type=="rawtext"):
            mic = RawTextMic()
            return mic.activeListenToAllOptions(THRESHOLD,speak_callback)
        mic = ArecordMic()
        return mic.activeListenToAllOptions(THRESHOLD,speak_callback)

class RawTextMic:
    '''
    命令行文字输入代替语音输入,just dummy
    （测试调试使用,语音识别太费（¯﹃¯）口水)
    '''
    def __init__(self):
        pass

    def passiveListen(self, detected_word, transcribe_callback=None):
        return True,detected_word

    def activeListenToAllOptions(self, THRESHOLD=None, speak_callback=None, transcribe_callback=None):
        return [self.activeListen(THRESHOLD, speak_callback, transcribe_callback)]

    def activeListen(self, THRESHOLD=None, speak_callback=None, transcribe_callback=None):
        input = raw_input("YOU SAY: ")
        return input

class ArecordMic:
    '''
    通过arecord命令写入到buffer中，然后从buffer中获取音频数据给识别模块
    '''
    def __init__(self):
        self._logger = lib.util.init_logger(__name__)
        channel_num = 1
        rate = 16000
        self._ring_buffer = RingBuffer(channel_num*rate* 5)
        self.recording = False

    def terminate(self):
        self.recording = False
        self.record_thread.join()

    def arecord_process(self):
        CHUNK = 2048
        RECORD_RATE = 16000
        cmd = 'arecord -q -r %d -f S16_LE' % RECORD_RATE
        self._logger.debug(cmd)
        process = subprocess.Popen(cmd.split(' '),
                                   stdout = subprocess.PIPE,
                                   stderr = subprocess.PIPE)
        wav = wave.open(process.stdout, 'rb')
        while self.recording:
            data = wav.readframes(CHUNK)
            self._ring_buffer.extend(data)
        process.terminate()

    def init_recording(self):
        """
        开一个子线程用于将音频数据录入到共享的buffer里，然后主线程从buffer里头取出数据
        """
        self.recording = True
        self.record_thread = threading.Thread(target = self.arecord_process)
        self.record_thread.start()
    
    def passiveListen(self, detected_word, transcribe_callback=None):
        if type(detected_word) is not list:
            detected_word = [detected_word]
            data = self._ring_buffer.get()
            if len(data) == 0:
                time.sleep(0.05)
                return (None,None)
            if transcribe_callback is not None:
                transcribed = transcribe_callback(data)
            else:
                self._logger.error("passive listen no transcribe callback function")

            words = [word for word in detected_word if word in transcribed]

            if len(words)>0:
                return (True, detected_word)
        return (None, None)

    def activeListenToAllOptions(self, THRESHOLD=None, speak_callback=None, transcribe_callback=None):

        if speak_callback is not None:
            speak_callback(os.path.join(lib.appPath.DATA_PATH,"snowboy/resources/ding.wav"))

        data = self._ring_buffer.get()
        if len(data) == 0:
            return None

        if transcribe_callback is not None:
            transcribed = transcribe_callback(data)

        if speak_callback is not None:
            speak_callback(os.path.join(lib.appPath.DATA_PATH,"snowboy/resources/dong.wav"))

        return transcribed

class PyAudioMic:
    '''
    通过pyaudio封装的lib库，对音频文件写入临时文件中，提供给识别模块读取
    '''
    def __init__(self):
        self._logger = lib.util.init_logger(__name__)

        self._logger.info("Initializing PyAudio.")
        self._audio = pyaudio.PyAudio()
        self._logger.info("Initialization of PyAudio completed.")

    def __del__(self):
        self._audio.terminate()

    def getScore(self, data):
        rms = audioop.rms(data, 2)
        score = rms / 3
        return score

    def fetchThreshold(self):

        # TODO: Consolidate variables from the next three functions
        THRESHOLD_MULTIPLIER = 1.8
        RATE = 16000
        CHUNK = 1024
        THRESHOLD_TIME = 1

        stream = self._audio.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK)
        frames = []
        lastN = [i for i in range(20)]
        for i in range(0, RATE / CHUNK * THRESHOLD_TIME):
            data = stream.read(CHUNK)
            frames.append(data)
            lastN.pop(0)
            lastN.append(self.getScore(data))
            average = sum(lastN) / len(lastN)

        stream.stop_stream()
        stream.close()
        THRESHOLD = average * THRESHOLD_MULTIPLIER

        return THRESHOLD

    def passiveListen(self, detected_word, transcribe_callback=None):
        """
        Listens for detected_word in everyday sound. Times out after LISTEN_TIME, so
        needs to be restarted.
        """

        THRESHOLD_MULTIPLIER = 1.8
        RATE = 16000
        CHUNK = 1024
        THRESHOLD_TIME = 1
        LISTEN_TIME = 10

        stream = self._audio.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK)

        #step 1. 在设定的阈值时间内,计算一个音频片段的rms(均方根--音频信号中的功率的度量)值的平均阈值(这里设置1秒的时间，hi一下)
        frames = []
        lastN = [i for i in range(20)]
        for i in range(0, RATE / CHUNK * THRESHOLD_TIME):
            data = stream.read(CHUNK)
            frames.append(data)
            lastN.pop(0)
            lastN.append(self.getScore(data))
            average = sum(lastN) / len(lastN)
        THRESHOLD = average * THRESHOLD_MULTIPLIER
        self._logger.debug("lastN:{%s},average:{%d},THRESHOLD:{%d}",lastN,average,THRESHOLD)

        #step 2. 录取的音频片段的rms(均方根)值大于设定的阈值，则进行下步把这些录音片段用于语音识别；否则识别超时不成功
        frames = []
        rms = []
        didDetect = False
        for i in range(0, RATE / CHUNK * LISTEN_TIME):
            data = stream.read(CHUNK)
            frames.append(data)
            score = self.getScore(data)
            rms.append(score)
            if score > THRESHOLD:
                didDetect = True
                break
        self._logger.debug("rms_values:{%s},last_score:{%d},THRESHOLD:{%d}",rms,score,THRESHOLD)
        if not didDetect:
            print "No disturbance detected"
            stream.stop_stream()
            stream.close()
            return (None, None)

        #step 3. 开始识别
        # cutoff any recording before this disturbance was detected
        frames = frames[-20:]

        # otherwise, let's keep recording for few seconds and save the file
        DELAY_MULTIPLIER = 1
        for i in range(0, RATE / CHUNK * DELAY_MULTIPLIER):
            data = stream.read(CHUNK)
            frames.append(data)

        # save the audio data
        stream.stop_stream()
        stream.close()

        with tempfile.NamedTemporaryFile(mode='w+b') as f:
            wav_fp = wave.open(f, 'wb')
            wav_fp.setnchannels(1)
            wav_fp.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
            wav_fp.setframerate(RATE)
            wav_fp.writeframes(''.join(frames))
            wav_fp.close()
            f.seek(0)
            # check if detected_word was said
            if transcribe_callback is not None:
                transcribed = transcribe_callback(f)
            else:
                self._logger.error("passive listen no transcribe callback function")

        if any(detected_word in phrase for phrase in transcribed):
            return (THRESHOLD, detected_word)

        return (False, transcribed)

    def activeListen(self, THRESHOLD=None, speak_callback=None, transcribe_callback=None):
        """
            Records until a second of silence or times out after 12 seconds

            Returns the first matching string or None
        """

        options = self.activeListenToAllOptions(THRESHOLD,speak_callback,transcribe_callback)
        if options:
            return options[0]

    def activeListenToAllOptions(self, THRESHOLD=None, speak_callback=None, transcribe_callback=None):
        """
            Records until a second of silence or times out after 12 seconds

            Returns a list of the matching options or empty list
        """

        RATE = 16000
        CHUNK = 1024
        LISTEN_TIME = 12

        # check if no threshold provided
        if THRESHOLD is None or int(THRESHOLD)<=1:
            THRESHOLD = self.fetchThreshold()

        if speak_callback is not None:
            speak_callback(os.path.join(lib.appPath.DATA_PATH,"snowboy/resources/ding.wav"))

        # prepare recording stream
        stream = self._audio.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK)

        frames = []
        # increasing the range # results in longer pause after command
        lastN = [THRESHOLD * 1.2 for i in range(40)]

        for i in range(0, RATE / CHUNK * LISTEN_TIME):

            data = stream.read(CHUNK)
            frames.append(data)
            score = self.getScore(data)

            lastN.pop(0)
            lastN.append(score)

            average = sum(lastN) / float(len(lastN))

            # TODO: 0.8 should not be a MAGIC NUMBER!
            if average < THRESHOLD * 0.8:
                break

        if speak_callback is not None:
            speak_callback(os.path.join(lib.appPath.DATA_PATH,"snowboy/resources/dong.wav"))

        # save the audio data
        stream.stop_stream()
        stream.close()

        with tempfile.SpooledTemporaryFile(mode='w+b') as f:
            wav_fp = wave.open(f, 'wb')
            wav_fp.setnchannels(1)
            wav_fp.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
            wav_fp.setframerate(RATE)
            wav_fp.writeframes(''.join(frames))
            wav_fp.close()
            f.seek(0)
            frames = []
            if transcribe_callback is not None:
                transcribed = transcribe_callback(f)
            else:
                self._logger.error("passive listen no transcribe callback function")
            return transcribed

