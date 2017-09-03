#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json

url = "https://douban.fm/j/v2/playlist"

querystring = {"channel":"0","kbps":"128","client":"s:mainsite|y:3.0","app_name":"radio_website","version":"100","type":"p","sid":"695088","pt":"","pb":"128","apikey":""}

headers = {
        'host': "douban.fm",
        'connection': "keep-alive",
        'accept': "text/javascript, text/html, application/xml, text/xml, */*",
        'x-requested-with': "XMLHttpRequest",
        'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
        'content-type': "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
        'referer': "https://douban.fm/",
        'accept-encoding': "gzip, deflate, br",
        'accept-language': "zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4",
        'cookie': "bid=ha5ZoPgYmgM; flag=\"ok\"; ac=\"1504322797\"; dbcl2=\"3867696:fVfJ9GW24NM\"; ck=Mz4D; _ga=GA1.2.1921561123.1504322809; _gid=GA1.2.286750020.1504322809",
        'cache-control': "no-cache",
        }

response = requests.request("GET", url, data='', headers=headers, params=querystring)

print(json.loads(response.text)['song'][0]['albumtitle'].encode('UTF-8'))
