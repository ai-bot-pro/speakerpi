#!/bin/bash
[ $# -ne 1 ] && echo "need param music url" && exit

MPLAYER=`which mplayer`

if [ "x$MPLAYER" = "x" ];then
  echo "no mplayer bin, installing...\n"
  sudo apt-get install mplayer
fi
LC_ALL=C

url=$1
echo $url
MPLAYER=/usr/bin/mplayer
echo "$MPLAYER -slave -quiet -ao alsa $url"
$MPLAYER -slave -quiet -ao alsa $url

