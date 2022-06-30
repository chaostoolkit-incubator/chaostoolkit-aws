#!/bin/bash

#Mandatory parameters:
#param='delay 1000ms 500ms' or param='delay 1000ms 500ms' or param='corrupt 15%'
#duration=60

#Check if it is a normal setting
check=$(tc -s qdisc show dev $device |grep pfifo_fast)
ret=$?

#if not, recovery
if [ $ret -ne 0 ]; then
    tc qdisc del dev $device root 2>&1 >/dev/null
fi

#Do experiments
experiment=$(tc qdisc add dev $device root netem $param)
ret=$?
if [ $ret -eq 0 ]; then
    echo "experiment network ($param) -> <$instance_id>: success"
else
    echo "experiment network ($param) -> <$instance_id>: fail"
fi

#Sleep $duration
#Mandatory
sleep $duration

#recovery
tc -s qdisc show dev $device |grep pfifo_fast 2>&1 >/dev/null
ret1=$?
#if not, recovery
if [ $ret1 -ne 0 ]; then
    tc qdisc del dev $device root 2>&1 >/dev/null
fi

#Check if it is a normal setting
tc -s qdisc show dev $device |grep pfifo_fast 2>&1 >/dev/null
ret2=$?
if [ $ret2 -eq 0 ]; then
    echo "recover network ($param) -> <$instance_id>: success"
else
    echo "recover network ($param) -> <$instance_id>: fail"
fi