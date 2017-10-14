#!/bin/bash
######################################################
#if u use bluethooth speaker, u can use this script
#NOTICE: u need get bluethooth speaker MAC and pair && trust this MAC by bluetoothctl before run this script
#power on for this example(add follow scrpit in ~/.bashrc):
#robot_dir="/home/pi/doubanfm"
#bluetooth_mac="E8:07:BF:01:33:19"
#run=`ps -ef | grep "sh ${robot_dir}/run.sh" | grep -v grep`
#if [ x"$run" = x ];then
#  date=`date '+%Y%m%d%H%M%S'`
#  mv ${robot_dir}/log/robot.log ${robot_dir}/log/robot.${date}.log
#  nohup sh ${robot_dir}/run.sh ${bluetooth_mac} > ${robot_dir}/log/robot.log 2>&1 &
#  find ${robot_dir}/log/ -type f -name "robot.*.log" -ctime +3 | xargs rm -f
#  #rm_date=`date -d '2 days ago' +%Y%m%d`
#  #rm -f ${robot_dir}/log/robot.${rm_date}*.log
#fi
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

