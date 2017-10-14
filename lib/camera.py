# -*- coding: utf-8-*-
# use picamera 
# look this: http://picamera.readthedocs.io/en/release-1.2/recipes1.html
import io
import os
import time
import struct
import socket
import picamera
from PIL import Image
import numpy as np

try:
    import cv2
    import imutils
    from imutils.video.pivideostream import PiVideoStream
except ImportError:
    pass

import lib.appPath

class VideoCamera(object):
    def __init__(self, flip = False):
        self.vs = PiVideoStream().start()
        self.stop_status = False
        self.flip = flip
        #启动视频调制正常显示状态需要一些时间
        time.sleep(2.0)

    def __del__(self):
        if self.stop_status is False:
            self.stop()

    def stop(self):
        if self.stop_status is False:
            self.vs.stop()
            self.stop_status = True

    def flip_if_needed(self, frame):
        if self.flip:
            return np.flip(frame, 0)
        return frame

    def get_frame(self):
        frame = self.flip_if_needed(self.vs.read())
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()

    def get_object(self, classifier):
        found_objects = False
        frame = self.flip_if_needed(self.vs.read()).copy() 
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        #参数调整
        objects = classifier.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(objects) > 0:
            found_objects = True

        # Draw a rectangle around the objects
        for (x, y, w, h) in objects:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        return (jpeg.tobytes(), found_objects)


class PhotographCamera(object):
    def __init__(self):
        pass

    @classmethod
    def photographToFile(cls):
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
    
    @classmethod
    def photographToBytesIO(cls):
        #write stream to BytesIO(Python’s in-memory stream class)
        stream = io.BytesIO()
        with picamera.PiCamera() as camera:
            camera.start_preview()
            time.sleep(2)
            camera.capture(stream, format='jpeg')
        # "Rewind" the stream to the beginning so we can read its content
        stream.seek(0)

        # save
        image = Image.open(stream)
        image_file = os.path.join(lib.appPath.DATA_PATH, 'photo.jpg');
        image.save(image_file)

        stream.seek(0)
        return stream.read()
    
    @classmethod
    def photographToCV(cls):
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

    @classmethod
    def photographSeq(cls):
        with picamera.PiCamera() as camera:
            camera.start_preview()
            time.sleep(2)
            for filename in camera.capture_continuous('img{counter:03d}.jpg'):
                print('Captured %s' % filename)
                time.sleep(300) # wait 5 minutes
    
    @classmethod
    def photographToServerSocket(cls):
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
    
    @classmethod
    def photographToClientSocket(cls,server_address,port):
        client_socket = socket.socket()
        client_socket.connect((server_address, port))
    
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
