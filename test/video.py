#!/usr/bin/env python
# -*- coding: utf-8 -*-
# look this: http://picamera.readthedocs.io/en/release-1.2/recipes1.html

import io
import os
import sys
import random
import time
import struct
import socket
import picamera
import subprocess

def videoToFile():
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        camera.start_recording('my_video.h264')
        camera.wait_recording(10)
        camera.stop_recording()

def videoToBytesIO():
    stream = io.BytesIO()
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        camera.start_recording(stream, format='h264', quantization=23)
        camera.wait_recording(10)
        camera.stop_recording()

def videoToManyFiles():
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        camera.start_recording('1.h264')
        camera.wait_recording(5)
        for i in range(2, 11):
            camera.split_recording('%d.h264' % i)
            camera.wait_recording(5)

        camera.stop_recording()

def videoFullResolution():
    with picamera.PiCamera() as camera:
        camera.resolution = (2592, 1944)
        camera.start_recording('full_res.h264', resize=(1024, 768))
        camera.wait_recording(10)
        camera.stop_recording()

#u can see this: https://en.wikipedia.org/wiki/Circular_buffer
def videoToRingBufferForIO():
    def write_now():
        # Randomly return True (like a fake motion detection routine)
        return random.randint(0, 10) == 0

    def write_video(stream):
        print('Writing video!')
        with stream.lock:
            # Find the first header frame in the video
            for frame in stream.frames:
                if frame.header:
                    stream.seek(frame.position)
                    break
            # Write the rest of the stream to disk
            with io.open('motion.h264', 'wb') as output:
                output.write(stream.read())

    with picamera.PiCamera() as camera:
        stream = picamera.PiCameraCircularIO(camera, seconds=20)
        camera.start_recording(stream, format='h264')
        try:
            while True:
                camera.wait_recording(1)
                if write_now():
                    # Keep recording for 10 seconds and only then write the
                    # stream to disk
                    camera.wait_recording(10)
                    write_video(stream)
        finally:
            camera.stop_recording()

def videoToClientSocket():
    client_socket = socket.socket()
    client_socket.connect(('192.168.1.102', 8000))

    # Make a file-like object out of the connection
    connection = client_socket.makefile('wb')
    try:
        with picamera.PiCamera() as camera:
            camera.resolution = (640, 480)
            # Start a preview and let the camera warm up for 2 seconds
            camera.start_preview()
            time.sleep(2)
            # Start recording, sending the output to the connection for 60
            # seconds, then stop
            camera.start_recording(connection, format='h264')
            camera.wait_recording(60)
            camera.stop_recording()
    finally:
        connection.close()
        client_socket.close()

def videoToPlayerFromServerSocket():
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 8000))
    server_socket.listen(0)

    # Accept a single connection and make a file-like object out of it
    connection = server_socket.accept()[0].makefile('rb')
    try:
        # Run a viewer with an appropriate command line. Uncomment the mplayer
        # version if you would prefer to use mplayer instead of VLC
        cmdline = 'vlc --demux h264 -'
        #cmdline = 'mplayer -fps 31 -cache 1024 -'
        player = subprocess.Popen(cmdline.split(), stdin=subprocess.PIPE)
        while True:
            # Repeatedly read 1k of data from the connection and write it to
            # the media player's stdin
            data = connection.read(1024)
            if not data:
                break
            player.stdin.write(data)
    finally:
        connection.close()
        server_socket.close()
        player.terminate()


if __name__ == '__main__':
    #videoToFile()

    #videoToBytesIO()

    #videoToManyFiles()

    #videoToRingBufferForIO()

    videoToClientSocket()




