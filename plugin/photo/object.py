#!/usr/bin/env python
# -*- coding: utf-8 -*-
# look this: http://picamera.readthedocs.io/en/release-1.2/recipes1.html
import io
import os
import sys
import time
import struct
import socket
import picamera
from PIL import Image
import cv2
import numpy as np

import lib.appPath
from lib.graphic.baiduGraphic import BaiduGraphic

TAG = 'object'
CATE = 'photo'

def son_process_handle(speaker,get_text_callback):
    '''
    子进程处理逻辑
    speaker: voice实例(tts)
    get_text_callback: 获取文本指令回调函数
    '''
    print("<<<<<<< begin photo object son process handle >>>>>>>")

def send_handle(text,in_fp,son_processor,speaker):
    '''
    发送指令给子进程处理(pipe,signal)
    text: 指令
    in_fp: pipe 输入端
    son_processor: 子进程(Process 实例)
    speaker: voice实例(tts)
    '''
    print("<<<<<<< begin photo object send pipe handle >>>>>>>")
    baidu_graphic = BaiduGraphic.get_instance()
    detect_type = None
    if re.search(u'菜品', text): detect_type = "dish"
    if re.search(u'车', text): detect_type = "car"
    if re.search(u'植物', text): detect_type = "plant"
    if re.search(u'动物', text): detect_type = "animal"
    if re.search(u'标志', text): detect_type = "logo"
    
    #拍照
    img = photographToBytesIO()

    res = baidu_graphic.detectImage(img,detect_type) if detect_type is not None else None

    name = res['name'] if 'name' in res else None
    if name is not None:
        speaker.say("这个应该是"+name.encode("UTF-8"))
    else:
        speaker.say("没有识别出来，请放好点再试一次吧")

    in_fp.close()
    son_processor.join()
    pid_file = os.path.join(lib.appPath.DATA_PATH, __name__+'.pid');
    if os.path.exists(pid_file):
        os.remove(pid_file)

def isValid(text):
    valid_words = [
            u"这是什么菜品",
            u"这是什么车",
            u"这是什么植物",
            u"这是什么动物",
            u"这是什么标志",
        ]
    res = any(word in text for word in valid_words)
    return res

def photographToFile():
    # Explicitly open a new file called my_image.jpg
    my_file = open('photo.jpg', 'wb')
    with picamera.PiCamera() as camera:
        camera.start_preview()
        time.sleep(2)
        camera.capture(my_file)
        # Note that at this point the data is in the file cache, but may
        # not actually have been written to disk yet
    my_file.close()
    # Now the file has been closed, other processes should be able to
    #read the image successfully

    return True

def photographToBytesIO():
    #write stream to BytesIO(Python’s in-memory stream class)
    stream = io.BytesIO()
    with picamera.PiCamera() as camera:
        camera.start_preview()
        time.sleep(2)
        camera.capture(stream, format='jpeg')
    # "Rewind" the stream to the beginning so we can read its content
    stream.seek(0)
    return stream.read()

def photographToCV():
    # Create the in-memory stream
    stream = io.BytesIO()
    with picamera.PiCamera() as camera:
        camera.start_preview()
        time.sleep(2)
        camera.capture(stream, format='jpeg')
    # Construct a numpy array from the stream
    data = np.fromstring(stream.getvalue(), dtype=np.uint8)
    # "Decode" the image from the array, preserving colour
    image = cv2.imdecode(data, 1)
    # OpenCV returns an array with data in BGR order. If you want RGB instead
    # use the following...
    image = image[:, :, ::-1]

    return image

def photographSeq():
    with picamera.PiCamera() as camera:
        camera.start_preview()
        time.sleep(2)
        for filename in camera.capture_continuous('img{counter:03d}.jpg'):
            print('Captured %s' % filename)
            time.sleep(300) # wait 5 minutes

def photographToServerSocket():
    # NOTICE:  
    #   The server script should be run first (don't run in pi) 
    #   to ensure there’s a listening socket ready to accept a connection from the client script
    # Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
    # all interfaces)
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 8000))
    server_socket.listen(0)

    # Accept a single connection and make a file-like object out of it
    # @TODO: use select/poll  or use epoll for more connections 10k>
    connection = server_socket.accept()[0].makefile('rb')
    try:
        while True:
            # Read the length of the image as a 32-bit unsigned int. If the
            # length is zero, quit the loop
            image_len = struct.unpack('<L', connection.read(4))[0]
            if not image_len:
                break
            # Construct a stream to hold the image data and read the image
            # data from the connection
            image_stream = io.BytesIO()
            image_stream.write(connection.read(image_len))
            # Rewind the stream, open it as an image with PIL and do some
            # processing on it
            image_stream.seek(0)
            image = Image.open(image_stream)
            print('Image is %dx%d' % image.size)
            image.verify()
            print('Image is verified')
    finally:
        connection.close()
        server_socket.close()

def photographToClientSocket():
    # Connect a client socket to my_server:8000 (change my_server to the
    # hostname of your server)
    client_socket = socket.socket()
    #client_socket.connect(('my_server', 8000))
    client_socket.connect(('192.168.1.102', 8000))

    # Make a file-like object out of the connection
    connection = client_socket.makefile('wb')
    try:
        with picamera.PiCamera() as camera:
            camera.resolution = (640, 480)
            # Start a preview and let the camera warm up for 2 seconds
            camera.start_preview()
            time.sleep(2)
            
            # Note the start time and construct a stream to hold image data
            # temporarily (we could write it directly to connection but in this
            # case we want to find out the size of each capture first to keep
            # our protocol simple)
            start = time.time()
            stream = io.BytesIO()
            for foo in camera.capture_continuous(stream, 'jpeg'):
                # Write the length of the capture to the stream and flush to
                # ensure it actually gets sent
                connection.write(struct.pack('<L', stream.tell()))
                connection.flush()
                # Rewind the stream and send the image data over the wire
                stream.seek(0)
                connection.write(stream.read())
                # If we've been capturing for more than 30 seconds, quit
                if time.time() - start > 30:
                  break
                # Reset the stream for the next capture
                stream.seek(0)
                stream.truncate()
                # Write a length of zero to the stream to signal we're done
        connection.write(struct.pack('<L', 0))
    finally:
        connection.close()
        client_socket.close()
    

