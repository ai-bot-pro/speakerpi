# -*- coding: utf-8-*-

import sys
import argparse
import logging

from lib.voice.baiduVoice import BaiduVoice
from plugin.fm.doubanFM import DoubanFM

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='doubanFM pi')
    parser.add_argument('--debug', action='store_true',
                        help='Show debug messages')
    args = parser.parse_args()

    logging.basicConfig(stream=sys.stdout)
    if args.debug:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

    baidu_voice = BaiduVoice.get_instance()
    douban_fm = DoubanFM.get_instance()

    baidu_voice.say("开始播放豆瓣电台")

    for i in range(0,100):
        douban_fm.playNextSong()

    

