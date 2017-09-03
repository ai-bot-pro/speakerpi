#!/bin/bash

url=`curl "https://api.douban.com/v2/fm/playlist?alt=json&apikey=02646d3fb69a52ff072d47bf23cef8fd&app_name=radio_iphone&channel=110&client=s%3Amobile%7Cy%3AiOS%2010.2%7Cf%3A115%7Cd%3Ab88146214e19b8a8244c9bc0e2789da68955234d%7Ce%3AiPhone7%2C1%7Cm%3Aappstore&douban_udid=b635779c65b816b13b330b68921c0f8edc049590&formats=aac&kbps=128&pt=0.0&type=n&udid=b88146214e19b8a8244c9bc0e2789da68955234d&version=115" | jq .song[0].url`

echo "sh playDoubanfm.sh $url"

sh playDoubanfm.sh $url
