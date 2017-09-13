# -*- coding: utf-8-*-
# from jasper mic.py change sm
import os
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

class RawTextMic:
    '''
    命令行文字输入代替语音输入（测试调试使用,语音识别太费（¯﹃¯）口水)
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

class Mic:
    '''
    两种语音录入方式(命令arecord方式,暂时未开发; 利用pyaudio库,默认频率16000Hz)
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

        # number of seconds to allow to establish threshold
        THRESHOLD_TIME = 1

        # prepare recording stream
        stream = self._audio.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK)

        # stores the audio data
        frames = []

        # stores the lastN score values
        lastN = [i for i in range(20)]

        # calculate the long run average, and thereby the proper threshold
        for i in range(0, RATE / CHUNK * THRESHOLD_TIME):

            data = stream.read(CHUNK)
            frames.append(data)

            # save this data point as a score
            lastN.pop(0)
            lastN.append(self.getScore(data))
            average = sum(lastN) / len(lastN)

        stream.stop_stream()
        stream.close()

        # this will be the benchmark to cause a disturbance over!
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

        # number of seconds to allow to establish threshold
        THRESHOLD_TIME = 1

        # number of seconds to listen before forcing restart
        LISTEN_TIME = 10

        # prepare recording stream
        stream = self._audio.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK)

        # stores the audio data
        frames = []

        # stores the lastN score values
        lastN = [i for i in range(30)]

        # calculate the long run average, and thereby the proper threshold
        for i in range(0, RATE / CHUNK * THRESHOLD_TIME):

            data = stream.read(CHUNK)
            frames.append(data)

            # save this data point as a score
            lastN.pop(0)
            lastN.append(self.getScore(data))
            average = sum(lastN) / len(lastN)

        # this will be the benchmark to cause a disturbance over!
        THRESHOLD = average * THRESHOLD_MULTIPLIER

        # save some memory for sound data
        frames = []

        # flag raised when sound disturbance detected
        didDetect = False

        # start passively listening for disturbance above threshold
        for i in range(0, RATE / CHUNK * LISTEN_TIME):

            data = stream.read(CHUNK)
            frames.append(data)
            score = self.getScore(data)

            if score > THRESHOLD:
                didDetect = True
                break

        # no use continuing if no flag raised
        if not didDetect:
            print "No disturbance detected"
            stream.stop_stream()
            stream.close()
            return (None, None)

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
        if THRESHOLD is None:
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
        # generation
        lastN = [THRESHOLD * 1.2 for i in range(30)]

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
            # check if detected_word was said
            if transcribe_callback is not None:
                transcribed = transcribe_callback(f)
            else:
                self._logger.error("passive listen no transcribe callback function")
            return transcribed

    def arecod_process(self):
        CHUNK = 2048
        RECORD_RATE = 16000
        cmd = 'arecord -q -r %d -f S16_LE' % RECORD_RATE
        process = subprocess.Popen(cmd.split(' '),
                                   stdout = subprocess.PIPE,
                                   stderr = subprocess.PIPE)
        wav = wave.open(process.stdout, 'rb')
        while self.recording:
            data = wav.readframes(CHUNK)
            self.ring_buffer.extend(data)
        process.terminate()

    def init_recording(self):
        """
        Start a thread for spawning arecord process and reading its stdout
        """
        self.recording = True
        self.record_thread = threading.Thread(target = self.record_proc)
        self.record_thread.start()


