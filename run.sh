#!/bin/bash
######################################################
#if u use bluethooth speaker, u can use this script
#NOTICE: u need get bluethooth speaker MAC and pair && trust this MAC by bluetoothctl before run this script
#power on for this example(add follow scrpit in ~/.bashrc):
#  robot_dir="/home/pi/doubanfm"
#  run=`ps -ef | grep "sh ${robot_dir}/run.sh" | grep -v grep`
#  if [ x"$run" = x ];then
#    date=`date '+%Y%m%d%H%M%S'`
#    nohup sh ${robot_dir}/run.sh E8:07:BF:01:33:19 > ${robot_dir}/log/robot.${date}.log 2>&1 &
#  fi
#################################

[ $# -ne 1 ] && echo "need params bluetooth MAC" && exit
MAC=$1

pulseaudio=`which pulseaudio`
bluetoothctl=`which bluetoothctl`
amixer=`which amixer`
python=`which python`

cur_dir=`dirname $0`

pulseaudio_status=`ps -ef | grep -v grep | grep pulseaudio`
while [ x"$pulseaudio_status" = x ];do
  $pulseaudio -D
  sleep 3
  
  echo "connect ${MAC}" | $bluetoothctl -a
  sleep 5

  $amixer -D pulse sset Master 30%
  sleep 10

  pulseaudio_status=`ps -ef | grep -v grep | grep pulseaudio`
  echo $pulseaudio_status
done

$python ${cur_dir}/run.py 

